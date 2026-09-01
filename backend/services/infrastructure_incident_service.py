import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database import SessionLocal, InfrastructureIncidentModel, PaymentEventModel, LivePaymentModel

class InfrastructureIncidentService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(InfrastructureIncidentService, cls).__new__(cls)
            return cls._instance

    def process_payment_failure_incident(
        self,
        live_rec: Dict[str, Any],
        intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyzes real payment failure telemetry and creates/updates an infrastructure incident in SQLite.
        Logs INFRASTRUCTURE_INCIDENT_DETECTED event in the payment timeline.
        """
        with self._lock:
            db = SessionLocal()
            try:
                payment_id = str(live_rec.get("payment_id") or "pay_unknown")
                merchant_id = str(live_rec.get("merchant_id") or "m_1004")
                gateway = str(live_rec.get("bank") or live_rec.get("gateway") or "SBI")
                payment_method = str(live_rec.get("payment_method") or "UPI")
                error_code = str(live_rec.get("error_code") or "BAD_REQUEST_TIMEOUT")
                error_desc = str(live_rec.get("error_description") or "UPI PSP Timeout")
                amount_inr = float(live_rec.get("amount_inr") or live_rec.get("amount") or 500.0)

                root_cause_obj = intelligence.get("root_cause") or {}
                recommendation_obj = intelligence.get("recommendation") or {}

                primary_rc = root_cause_obj.get("primary_root_cause") or {}
                root_cause_text = (
                    primary_rc.get("title") or
                    primary_rc.get("reason") or
                    root_cause_obj.get("root_cause") or
                    root_cause_obj.get("title") or
                    "Bank Gateway Network Handshake Timeout"
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

                err_code_lower = error_code.lower()
                err_desc_lower = error_desc.lower()

                # Determine Title and Severity dynamically based on telemetry
                if "international" in err_code_lower or "international" in err_desc_lower or "card_not_supported" in err_code_lower or "not_allowed" in err_code_lower:
                    title = f"{gateway} Card Restriction Spike"
                    severity = "WARNING"
                elif "upi" in payment_method.lower() or "timeout" in err_code_lower or "timeout" in err_desc_lower:
                    title = f"{gateway} UPI PSP Timeout Spike"
                    severity = "CRITICAL" if amount_inr >= 1000 or "timeout" in err_code_lower else "WARNING"
                elif "otp" in err_code_lower or "3ds" in err_code_lower:
                    title = f"{gateway} Card OTP/3DS Delivery Timeout Spike"
                    severity = "WARNING"
                else:
                    title = f"{gateway} Gateway Degradation Spike"
                    severity = "WARNING"

                # Check if an existing ACTIVE incident exists for this gateway within last 24h
                cutoff = datetime.utcnow() - timedelta(hours=24)
                existing = db.query(InfrastructureIncidentModel).filter(
                    InfrastructureIncidentModel.gateway == gateway,
                    InfrastructureIncidentModel.status == "ACTIVE",
                    InfrastructureIncidentModel.created_at >= cutoff
                ).first()

                if existing:
                    # Update aggregated telemetry
                    existing.affected_transactions_count += 1
                    existing.amount_at_risk += amount_inr
                    existing.updated_at = datetime.utcnow()
                    incident_model = existing
                else:
                    # Create new incident
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
                        severity=severity,
                        confidence=confidence_score,
                        root_cause=root_cause_text,
                        amount_at_risk=amount_inr,
                        recommended_mitigation=recommended_mitigation,
                        status="ACTIVE",
                        source="razorpay_test_webhook",
                        affected_transactions_count=1,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(incident_model)

                # Log INFRASTRUCTURE_INCIDENT_DETECTED timeline event
                incident_evt = PaymentEventModel(
                    payment_id=payment_id,
                    merchant_id=merchant_id,
                    event_type="INFRASTRUCTURE_INCIDENT_DETECTED",
                    event_description=f"Infrastructure Incident Detected: {title} ({severity}). Impact: ₹{amount_inr:,.2f} at risk.",
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
                        "gateway": "SBI",
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
                # Find matching incident record
                inc = db.query(InfrastructureIncidentModel).filter(
                    (InfrastructureIncidentModel.incident_id == incident_id) |
                    (InfrastructureIncidentModel.id == incident_id)
                ).first()

                gateway = inc.gateway if inc else "SBI"
                title = inc.title if inc else "SBI UPI PSP Timeout Spike"
                amount_at_risk = float(inc.amount_at_risk) if inc else 8110.0
                total_txns = inc.affected_transactions_count if inc else 9
                status = inc.status if inc else "ACTIVE"
                source = inc.source if inc else "razorpay_test_webhook"
                primary_payment_id = inc.payment_id if inc else None

                # Query live payments from SQLite
                live_service = get_live_payment_service()
                live_records = db.query(LivePaymentModel).filter(
                    (LivePaymentModel.bank == gateway) |
                    (LivePaymentModel.payment_id == primary_payment_id)
                ).order_by(LivePaymentModel.updated_at.desc()).all()

                payments = []
                for lp in live_records:
                    pm_dict = live_service._model_to_dict(lp, db)
                    if pm_dict:
                        payments.append(pm_dict)

                # Fallback demo payments if SQLite records are empty
                if not payments:
                    now = datetime.utcnow()
                    demo_payments = [
                        {
                            "payment_id": primary_payment_id or "pay_live_TWPT6ygiPSnSXh",
                            "merchant_id": "m_1004",
                            "amount": 1000.0,
                            "amount_inr": 1000.0,
                            "currency": "INR",
                            "status": "failed",
                            "payment_method": "Card" if "Card" in (inc.payment_method if inc else "") else "UPI",
                            "bank": gateway,
                            "error_code": inc.error_code if inc else "international_transaction_not_allowed",
                            "error_description": inc.root_cause if inc else "International cards are not supported",
                            "source": source,
                            "created_at": (now - timedelta(minutes=15)).isoformat(),
                            "updated_at": (now - timedelta(minutes=15)).isoformat(),
                        },
                        {
                            "payment_id": "pay_live_DEMO_98214",
                            "merchant_id": "m_1004",
                            "amount": 4250.0,
                            "amount_inr": 4250.0,
                            "currency": "INR",
                            "status": "failed",
                            "payment_method": "UPI",
                            "bank": gateway,
                            "error_code": "BAD_REQUEST_TIMEOUT",
                            "error_description": f"{gateway} Gateway Timeout Response (504)",
                            "source": "demo_seed",
                            "created_at": (now - timedelta(hours=1)).isoformat(),
                            "updated_at": (now - timedelta(hours=1)).isoformat(),
                        },
                        {
                            "payment_id": "pay_live_DEMO_98190",
                            "merchant_id": "m_1004",
                            "amount": 2860.0,
                            "amount_inr": 2860.0,
                            "currency": "INR",
                            "status": "failed",
                            "payment_method": "UPI",
                            "bank": gateway,
                            "error_code": "GATEWAY_INTERNAL_ERROR",
                            "error_description": f"{gateway} PSP Server Latency Spike",
                            "source": "demo_seed",
                            "created_at": (now - timedelta(hours=2)).isoformat(),
                            "updated_at": (now - timedelta(hours=2)).isoformat(),
                        }
                    ]
                    payments = demo_payments

                return {
                    "incident_id": incident_id,
                    "title": title,
                    "gateway": gateway,
                    "status": status,
                    "source": source,
                    "total_transactions": max(total_txns, len(payments)),
                    "total_amount_at_risk": amount_at_risk,
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

                if record:
                    record.status = "MITIGATED"
                    record.mitigated_at = datetime.utcnow()
                    record.updated_at = datetime.utcnow()

                    # Log MITIGATION_EXECUTED timeline event for primary payment and live payments on this gateway
                    if record.payment_id or record.gateway:
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
            "description": f"{record.gateway} gateway telemetry detected {record.error_code or 'failures'}. AI Root Cause: {record.root_cause}.",
            "root_cause": record.root_cause,
            "estimatedRevenueImpact": float(record.amount_at_risk),
            "amount_at_risk": float(record.amount_at_risk),
            "recommendedAction": record.recommended_mitigation,
            "recommended_mitigation": record.recommended_mitigation,
            "status": record.status,
            "source": record.source,
            "affectedMerchants": 1,
            "impactedTransactions": record.affected_transactions_count,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            "mitigated_at": record.mitigated_at.isoformat() if record.mitigated_at else None
        }

def get_infrastructure_incident_service() -> InfrastructureIncidentService:
    return InfrastructureIncidentService()
