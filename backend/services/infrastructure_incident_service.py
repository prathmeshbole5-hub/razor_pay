import json
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database import SessionLocal, InfrastructureIncidentModel, PaymentEventModel, LivePaymentModel
from services.internal_service import normalize_gateway_name

INCIDENT_GROUPING_WINDOW_MINUTES = 30

class InfrastructureIncidentService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(InfrastructureIncidentService, cls).__new__(cls)
            return cls._instance

    def _calculate_grouping_details(
        self,
        gateway_str: str,
        payment_method: str,
        error_code: str,
        error_desc: str
    ):
        gateway = normalize_gateway_name(gateway_str)
        err_code_lower = (error_code or "").lower()
        err_desc_lower = (error_desc or "").lower()
        method_lower = (payment_method or "").lower()

        if "international" in err_code_lower or "international" in err_desc_lower or "card_not_supported" in err_code_lower or "not_allowed" in err_code_lower:
            category = "CARD_RESTRICTION"
            title = f"{gateway} Card Restriction Spike"
            severity = "WARNING"
        elif "upi" in method_lower or "timeout" in err_code_lower or "timeout" in err_desc_lower:
            category = "TIMEOUT"
            title = f"{gateway} UPI PSP Timeout Spike" if "upi" in method_lower else f"{gateway} Gateway Timeout Spike"
            severity = "CRITICAL" if "timeout" in err_code_lower else "WARNING"
        elif "otp" in err_code_lower or "3ds" in err_code_lower:
            category = "OTP_DELIVERY_FAILURE"
            title = f"{gateway} Card OTP/3DS Delivery Timeout Spike"
            severity = "WARNING"
        else:
            category = "DEGRADATION"
            title = f"{gateway} Gateway Degradation Spike"
            severity = "WARNING"

        grouping_key = f"{gateway}:{category}"
        return gateway, category, title, severity, grouping_key

    def process_payment_failure_incident(
        self,
        live_rec: Dict[str, Any],
        intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyzes real payment failure telemetry and creates/updates a grouped infrastructure incident in SQLite.
        Groups related payment failures sharing gateway + error category within a 30-minute window.
        Logs INFRASTRUCTURE_INCIDENT_DETECTED event in the payment timeline.
        """
        with self._lock:
            db = SessionLocal()
            try:
                payment_id = str(live_rec.get("payment_id") or "pay_unknown")
                merchant_id = str(live_rec.get("merchant_id") or "m_1004")
                raw_gateway = str(live_rec.get("bank") or live_rec.get("gateway") or "SBI")
                payment_method = str(live_rec.get("payment_method") or "UPI")
                error_code = str(live_rec.get("error_code") or "BAD_REQUEST_TIMEOUT")
                error_desc = str(live_rec.get("error_description") or "UPI PSP Timeout")
                amount_inr = float(live_rec.get("amount_inr") or live_rec.get("amount") or 500.0)

                gateway, category, title, default_severity, grouping_key = self._calculate_grouping_details(
                    raw_gateway, payment_method, error_code, error_desc
                )

                root_cause_obj = intelligence.get("root_cause") or {}
                recommendation_obj = intelligence.get("recommendation") or {}

                primary_rc = root_cause_obj.get("primary_root_cause") or {}
                root_cause_text = (
                    primary_rc.get("title") or
                    primary_rc.get("reason") or
                    root_cause_obj.get("root_cause") or
                    root_cause_obj.get("title") or
                    f"{gateway} Network Handshake Timeout"
                )
                confidence_score = float(
                    primary_rc.get("confidence") or
                    root_cause_obj.get("confidence_score") or
                    intelligence.get("prediction", {}).get("confidence_score") or
                    0.94
                )

                rec_strat = recommendation_obj.get("recommended_strategy") or {}
                recommended_mitigation = (
                    rec_strat.get("strategy") or
                    rec_strat.get("action") or
                    "Automated Route Reroute: Direct transactions through a healthy gateway"
                )

                # Search active incident within recent 30-minute grouping window
                cutoff = datetime.utcnow() - timedelta(minutes=INCIDENT_GROUPING_WINDOW_MINUTES)
                existing = db.query(InfrastructureIncidentModel).filter(
                    InfrastructureIncidentModel.status == "ACTIVE",
                    InfrastructureIncidentModel.updated_at >= cutoff
                ).all()

                # Filter matching grouping_key or gateway+title in memory
                matching_inc = None
                for inc in existing:
                    if inc.grouping_key == grouping_key or (inc.gateway == gateway and inc.title == title):
                        matching_inc = inc
                        break

                if matching_inc:
                    # Parse affected payment IDs list
                    affected_ids = []
                    if matching_inc.affected_payment_ids:
                        try:
                            affected_ids = json.loads(matching_inc.affected_payment_ids)
                        except Exception:
                            affected_ids = [matching_inc.payment_id]
                    else:
                        affected_ids = [matching_inc.payment_id]

                    # Prevent Duplicate Processing
                    if payment_id not in affected_ids:
                        affected_ids.append(payment_id)
                        matching_inc.affected_payment_ids = json.dumps(affected_ids)

                        # Query all affected payments to recalculate aggregated amount & unique merchant count
                        affected_recs = db.query(LivePaymentModel).filter(
                            LivePaymentModel.payment_id.in_(affected_ids)
                        ).all()

                        failed_recs = [p for p in affected_recs if str(p.status or "").lower() == "failed"]
                        matching_inc.affected_transactions_count = len(affected_ids)
                        matching_inc.amount_at_risk = float(sum(p.amount or 0.0 for p in failed_recs)) if failed_recs else (matching_inc.amount_at_risk + amount_inr)
                        
                        merchant_set = set(p.merchant_id for p in affected_recs if p.merchant_id)
                        if merchant_id:
                            merchant_set.add(merchant_id)
                        matching_inc.impacted_merchants_count = max(1, len(merchant_set))

                        # Elevate severity if volume/impact spikes
                        if len(affected_ids) >= 3 or matching_inc.amount_at_risk >= 10000.0:
                            matching_inc.severity = "CRITICAL"

                    matching_inc.updated_at = datetime.utcnow()
                    incident_model = matching_inc
                else:
                    # Create new Infrastructure Incident
                    clean_id = payment_id.replace("pay_live_", "").replace("pay_", "")
                    incident_id = f"inc_{clean_id}"

                    incident_model = InfrastructureIncidentModel(
                        incident_id=incident_id,
                        payment_id=payment_id,
                        merchant_id=merchant_id,
                        gateway=gateway,
                        payment_method=payment_method,
                        error_code=error_code,
                        error_reason=live_rec.get("error_reason"),
                        title=title,
                        severity=default_severity,
                        confidence=confidence_score,
                        root_cause=root_cause_text,
                        amount_at_risk=amount_inr,
                        recommended_mitigation=recommended_mitigation,
                        status="ACTIVE",
                        source="razorpay_test_webhook",
                        affected_transactions_count=1,
                        grouping_key=grouping_key,
                        affected_payment_ids=json.dumps([payment_id]),
                        impacted_merchants_count=1,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(incident_model)

                # Log INFRASTRUCTURE_INCIDENT_DETECTED timeline event
                incident_evt = PaymentEventModel(
                    payment_id=payment_id,
                    merchant_id=merchant_id,
                    event_type="INFRASTRUCTURE_INCIDENT_DETECTED",
                    event_description=f"Infrastructure Incident Detected: {title} ({incident_model.severity}). Grouped impact: ₹{incident_model.amount_at_risk:,.2f} at risk across {incident_model.affected_transactions_count} transaction(s).",
                    created_at=datetime.utcnow()
                )
                db.add(incident_evt)

                db.commit()
                db.refresh(incident_model)
                return self._model_to_dict(incident_model)
            finally:
                db.close()

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        """
        Retrieves all infrastructure incidents from SQLite DB, formatted for Razorpay Internal Portal.
        Includes both real test webhook incidents and seeded demo incidents.
        """
        with self._lock:
            db = SessionLocal()
            try:
                records = db.query(InfrastructureIncidentModel).order_by(
                    InfrastructureIncidentModel.created_at.desc()
                ).all()

                result = [self._model_to_dict(r) for r in records]

                # Seed demo incident if DB is empty to maintain demo continuity
                if not result:
                    demo_inc = {
                        "id": "anom_101",
                        "incident_id": "anom_101",
                        "severity": "CRITICAL",
                        "title": "SBI Card OTP 3DS Delivery Timeout Spike",
                        "description": "SBI 3D-Secure SMS gateway latency has exceeded 3,800ms, causing massive OTP expiration for credit card authorizations.",
                        "affectedMerchants": 310,
                        "impactedTransactions": 14200,
                        "estimatedRevenueImpact": 42500000,
                        "confidenceScore": 98,
                        "recommendedAction": "Automated Route Reroute: Direct SBI card transactions to Visa Direct Tokenized 1-Click Auth.",
                        "status": "ACTIVE",
                        "source": "demo_seed",
                        "gateway": "SBI Card Gateway",
                        "payment_id": "pay_demo_sbi_01",
                        "created_at": datetime.utcnow().isoformat()
                    }
                    result.append(demo_inc)

                return result
            finally:
                db.close()

    def get_affected_payments(self, incident_id: str) -> Dict[str, Any]:
        """
        Retrieves all live persisted payments associated with a specific infrastructure incident.
        Includes full payment metadata and AI intelligence attached.
        """
        from services.live_payment_service import get_live_payment_service
        with self._lock:
            db = SessionLocal()
            try:
                inc = db.query(InfrastructureIncidentModel).filter(
                    (InfrastructureIncidentModel.incident_id == incident_id) |
                    (InfrastructureIncidentModel.id == incident_id)
                ).first()

                if not inc and not incident_id.startswith("inc_demo"):
                    return None

                gateway = inc.gateway if inc else "SBI Card Gateway"
                title = inc.title if inc else "SBI UPI PSP Timeout Spike"
                amount_at_risk = float(inc.amount_at_risk) if inc else 8110.0
                total_txns = inc.affected_transactions_count if inc else 1
                status = inc.status if inc else "ACTIVE"
                source = inc.source if inc else "razorpay_test_webhook"
                primary_payment_id = inc.payment_id if inc else None
                merchants_cnt = getattr(inc, 'impacted_merchants_count', 1) if inc else 1

                # Parse affected_payment_ids
                affected_ids = []
                if inc and inc.affected_payment_ids:
                    try:
                        affected_ids = json.loads(inc.affected_payment_ids)
                    except Exception:
                        if primary_payment_id:
                            affected_ids = [primary_payment_id]
                elif primary_payment_id:
                    affected_ids = [primary_payment_id]

                live_service = get_live_payment_service()
                payments = []

                if affected_ids:
                    live_records = db.query(LivePaymentModel).filter(
                        LivePaymentModel.payment_id.in_(affected_ids)
                    ).order_by(LivePaymentModel.updated_at.desc()).all()

                    for lp in live_records:
                        pm_dict = live_service._model_to_dict(lp, db)
                        if pm_dict:
                            payments.append(pm_dict)

                # Fallback to gateway matching if affected_ids was empty
                if not payments:
                    live_records = db.query(LivePaymentModel).filter(
                        (LivePaymentModel.bank == gateway) |
                        (LivePaymentModel.payment_id == primary_payment_id)
                    ).order_by(LivePaymentModel.updated_at.desc()).all()

                    for lp in live_records:
                        pm_dict = live_service._model_to_dict(lp, db)
                        if pm_dict:
                            payments.append(pm_dict)

                return {
                    "incident_id": incident_id,
                    "title": title,
                    "gateway": gateway,
                    "status": status,
                    "source": source,
                    "total_transactions": max(total_txns, len(payments)),
                    "total_amount_at_risk": amount_at_risk,
                    "impacted_merchants": merchants_cnt,
                    "payments": payments
                }
            finally:
                db.close()

    def mitigate_incident(self, incident_id: str) -> Dict[str, Any]:
        """
        Executes simulated emergency mitigation on an infrastructure incident.
        Updates status to MITIGATED and records MITIGATION_EXECUTED timeline event.
        """
        with self._lock:
            db = SessionLocal()
            try:
                record = db.query(InfrastructureIncidentModel).filter(
                    (InfrastructureIncidentModel.incident_id == incident_id) |
                    (InfrastructureIncidentModel.id == incident_id)
                ).first()

                if not record and not incident_id.startswith("inc_demo"):
                    return None

                if record:
                    record.status = "MITIGATED"
                    record.mitigated_at = datetime.utcnow()
                    record.updated_at = datetime.utcnow()

                    # Parse affected_payment_ids or find linked payments
                    affected_ids = []
                    if record.affected_payment_ids:
                        try:
                            affected_ids = json.loads(record.affected_payment_ids)
                        except Exception:
                            affected_ids = [record.payment_id] if record.payment_id else []

                    live_payments = []
                    if affected_ids:
                        live_payments = db.query(LivePaymentModel).filter(
                            LivePaymentModel.payment_id.in_(affected_ids)
                        ).all()
                    else:
                        live_payments = db.query(LivePaymentModel).filter(
                            (LivePaymentModel.payment_id == record.payment_id) |
                            (LivePaymentModel.bank == record.gateway)
                        ).all()

                    for lp in live_payments:
                        mit_evt = PaymentEventModel(
                            payment_id=lp.payment_id,
                            merchant_id=lp.merchant_id or record.merchant_id or "m_1004",
                            event_type="MITIGATION_EXECUTED",
                            event_description=f"Emergency Gateway Mitigation Reroute Executed for {record.gateway} (SIMULATION MODE).",
                            created_at=datetime.utcnow()
                        )
                        db.add(mit_evt)

                    db.commit()
                    db.refresh(record)
                    return {
                        "status": "mitigated",
                        "mode": "test_simulation",
                        "action": "gateway_reroute",
                        "incident_id": record.incident_id,
                        "message": f"Gateway reroute simulated successfully for {record.gateway}."
                    }
                else:
                    return {
                        "status": "mitigated",
                        "mode": "test_simulation",
                        "action": "gateway_reroute",
                        "incident_id": incident_id,
                        "message": "Gateway reroute simulated successfully (demo mode)."
                    }
            finally:
                db.close()

    def _model_to_dict(self, record: InfrastructureIncidentModel) -> Dict[str, Any]:
        conf_pct = int(record.confidence * 100) if record.confidence <= 1.0 else int(record.confidence)
        merchants_cnt = getattr(record, 'impacted_merchants_count', 1) or 1

        return {
            "id": record.incident_id,
            "incident_id": record.incident_id,
            "payment_id": record.payment_id,
            "merchant_id": record.merchant_id,
            "gateway": record.gateway,
            "payment_method": record.payment_method,
            "error_code": record.error_code,
            "error_reason": record.error_reason,
            "title": record.title,
            "severity": record.severity,
            "confidenceScore": conf_pct,
            "description": f"{record.gateway} telemetry detected {record.error_code or 'failures'}. AI Root Cause: {record.root_cause}.",
            "root_cause": record.root_cause,
            "estimatedRevenueImpact": float(record.amount_at_risk),
            "amount_at_risk": float(record.amount_at_risk),
            "recommendedAction": record.recommended_mitigation,
            "recommended_mitigation": record.recommended_mitigation,
            "status": record.status,
            "source": record.source,
            "affectedMerchants": merchants_cnt,
            "impactedTransactions": record.affected_transactions_count,
            "grouping_key": record.grouping_key,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            "mitigated_at": record.mitigated_at.isoformat() if record.mitigated_at else None
        }

def get_infrastructure_incident_service() -> InfrastructureIncidentService:
    return InfrastructureIncidentService()

