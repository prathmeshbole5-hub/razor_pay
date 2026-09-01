import pandas as pd
from typing import Dict, Any, List
from services.data_service import get_data_service

GATEWAY_HEALTH_THRESHOLDS = {
    "DEGRADED_FAILURE_RATE_PCT": 15.0,
    "DEGRADED_RECENT_FAILURES": 3,
    "OUTAGE_FAILURE_RATE_PCT": 50.0,
    "OUTAGE_RECENT_FAILURES": 8,
}

def normalize_gateway_name(gw_str: str) -> str:
    if not gw_str:
        return "Razorpay Gateway"
    s = str(gw_str).strip()
    s_upper = s.upper()
    if "SBI" in s_upper or "STATE BANK" in s_upper:
        return "SBI Card Gateway"
    elif "HDFC" in s_upper:
        return "HDFC Gateway"
    elif "ICICI" in s_upper:
        return "ICICI UPI"
    elif "AXIS" in s_upper:
        return "Axis Wallet"
    elif "RAZORPAY" in s_upper or "TEST" in s_upper:
        return "Razorpay Gateway"
    return s

class InternalService:
    def __init__(self):
        self.ds = get_data_service()

    def get_dashboard(self) -> Dict[str, Any]:
        payments = self.ds.get_payments()
        recovery = self.ds.get_recovery_attempts()
        gateway_events = self.ds.get_gateway_events()

        total_transactions = len(payments)
        successful_transactions = int((payments['status'] == 'Success').sum())
        failed_transactions = int((payments['status'] == 'Failed').sum())
        total_payment_volume = float(payments['amount_inr'].sum())

        overall_success_rate = round((successful_transactions / total_transactions * 100), 2) if total_transactions > 0 else 0.0
        overall_failure_rate = round((failed_transactions / total_transactions * 100), 2) if total_transactions > 0 else 0.0

        total_revenue_at_risk = float(recovery['risk_amount_inr'].sum())
        total_revenue_recovered = float(recovery['recovered_amount_inr'].sum())

        total_risk = total_revenue_at_risk + total_revenue_recovered
        overall_recovery_rate = round((total_revenue_recovered / total_risk * 100), 2) if total_risk > 0 else 0.0

        # Active incidents based on latest event per gateway + SQLite active incidents
        latest_events = gateway_events.sort_values('timestamp').groupby('gateway').last()
        csv_active_incidents = int((latest_events['is_incident'] == True).sum())

        try:
            from services.infrastructure_incident_service import get_infrastructure_incident_service
            db_incidents = get_infrastructure_incident_service().get_all_incidents()
            db_active_count = len([inc for inc in db_incidents if inc.get("status") == "ACTIVE"])
        except Exception:
            db_active_count = 0

        active_incidents = max(csv_active_incidents, db_active_count)

        return {
            "total_payment_volume": round(total_payment_volume, 2),
            "total_transactions": total_transactions,
            "successful_transactions": successful_transactions,
            "failed_transactions": failed_transactions,
            "overall_success_rate": overall_success_rate,
            "overall_failure_rate": overall_failure_rate,
            "total_revenue_at_risk": round(total_revenue_at_risk, 2),
            "total_revenue_recovered": round(total_revenue_recovered, 2),
            "overall_recovery_rate": overall_recovery_rate,
            "active_incidents": active_incidents
        }

    def get_gateway_health(self) -> List[Dict[str, Any]]:
        STANDARD_GATEWAYS = [
            "SBI Card Gateway",
            "HDFC Gateway",
            "ICICI UPI",
            "Axis Wallet",
            "Razorpay Gateway"
        ]

        # 1. Fetch real live payments & active incidents from SQLite DB
        live_payments = []
        active_incidents = []
        try:
            from database import SessionLocal, LivePaymentModel, InfrastructureIncidentModel
            db = SessionLocal()
            try:
                live_payments = db.query(LivePaymentModel).all()
                active_incidents = db.query(InfrastructureIncidentModel).filter_by(status="ACTIVE").all()
            finally:
                db.close()
        except Exception as db_err:
            print(f"[GatewayHealth] Database read notice: {db_err}")

        # 2. Fetch CSV payment dataset and gateway telemetry events
        csv_payments = self.ds.get_payments()
        gateway_events = self.ds.get_gateway_events()

        # Map live payments by normalized gateway
        gw_live_map: Dict[str, List[Any]] = {gw: [] for gw in STANDARD_GATEWAYS}
        for p in live_payments:
            norm = normalize_gateway_name(p.bank or "Razorpay Gateway")
            if norm not in gw_live_map:
                gw_live_map[norm] = []
            gw_live_map[norm].append(p)

        # Map CSV payments by normalized gateway
        gw_csv_map: Dict[str, List[Any]] = {gw: [] for gw in STANDARD_GATEWAYS}
        if not csv_payments.empty:
            for _, row in csv_payments.iterrows():
                norm = normalize_gateway_name(row.get('gateway') or "Razorpay Gateway")
                if norm not in gw_csv_map:
                    gw_csv_map[norm] = []
                gw_csv_map[norm].append(row)

        # Map Telemetry Latency by normalized gateway
        gw_telemetry_latency: Dict[str, List[float]] = {gw: [] for gw in STANDARD_GATEWAYS}
        if not gateway_events.empty:
            for _, row in gateway_events.iterrows():
                norm = normalize_gateway_name(row.get('gateway'))
                if norm not in gw_telemetry_latency:
                    gw_telemetry_latency[norm] = []
                gw_telemetry_latency[norm].append(float(row.get('latency_ms', 150.0)))

        # Map Active Incident Severities & Risk by normalized gateway
        gw_incidents: Dict[str, List[Any]] = {gw: [] for gw in STANDARD_GATEWAYS}
        for inc in active_incidents:
            norm = normalize_gateway_name(inc.gateway)
            if norm not in gw_incidents:
                gw_incidents[norm] = []
            gw_incidents[norm].append(inc)

        all_gateways = list(STANDARD_GATEWAYS)
        for g_name in list(gw_live_map.keys()):
            if g_name not in all_gateways:
                all_gateways.append(g_name)

        result = []
        for gw_name in all_gateways:
            lp_list = gw_live_map.get(gw_name, [])
            csv_list = gw_csv_map.get(gw_name, [])
            inc_list = gw_incidents.get(gw_name, [])
            # Live payment metrics
            lp_failed = [p for p in lp_list if str(p.status or "").lower() == "failed"]
            lp_success = [p for p in lp_list if str(p.status or "").lower() in ("captured", "verified", "successful", "success")]
            
            # CSV payment metrics
            csv_failed = [r for r in csv_list if str(r.get("status") or "").lower() in ("failed", "failure")]
            csv_success = [r for r in csv_list if str(r.get("status") or "").lower() in ("success", "captured", "verified", "successful")]

            # Calculate metrics prioritizing live SQLite transactions
            if len(lp_list) > 0:
                total_txns = len(lp_list)
                failed_txns = len(lp_failed)
                success_txns = len(lp_success)
                recent_failure_count = len(lp_failed)
                failure_rate = float(round((failed_txns / total_txns * 100), 2)) if total_txns > 0 else 0.0
                lp_risk = sum(float(p.amount or 0.0) for p in lp_failed)
                inc_risk = sum(float(inc.amount_at_risk or 0.0) for inc in inc_list)
                amount_at_risk = float(round(max(lp_risk, inc_risk), 2))
                
                merchants = set(str(p.merchant_id) for p in lp_failed if p.merchant_id)
                impacted_merchants = len(merchants)
            else:
                total_txns = len(csv_list)
                failed_txns = len(csv_failed)
                success_txns = len(csv_success)
                recent_failure_count = len(inc_list)
                failure_rate = float(round((failed_txns / total_txns * 100), 2)) if total_txns > 0 else 0.0
                inc_risk = sum(float(inc.amount_at_risk or 0.0) for inc in inc_list)
                amount_at_risk = float(round(inc_risk, 2))

                merchants = set(str(r.get("merchant_id")) for r in csv_failed if r.get("merchant_id"))
                impacted_merchants = len(merchants)

            average_success_rate = float(round(100.0 - failure_rate, 2)) if total_txns > 0 else 100.0

            # Telemetry Latency (Separated from transaction metrics)
            latencies = gw_telemetry_latency.get(gw_name, [])
            avg_latency = float(round(sum(latencies) / len(latencies), 2)) if latencies else 150.0

            # Dominant Error
            errors = []
            for p in lp_failed:
                err = p.error_description or p.error_code
                if err:
                    errors.append(str(err))
            for r in csv_failed:
                err = r.get("failure_category") or r.get("error_code")
                if err:
                    errors.append(str(err))
            error_dominant = errors[-1] if errors else "NONE"

            # Determine Health Status using transparent thresholds & active incidents
            has_critical_inc = any(inc.severity == "CRITICAL" for inc in inc_list)
            has_warning_inc = any(inc.status == "ACTIVE" for inc in inc_list)

            if (
                has_critical_inc
                or failure_rate >= GATEWAY_HEALTH_THRESHOLDS["OUTAGE_FAILURE_RATE_PCT"]
                or recent_failure_count >= GATEWAY_HEALTH_THRESHOLDS["OUTAGE_RECENT_FAILURES"]
            ):
                current_status = "OUTAGE"
            elif (
                has_warning_inc
                or failure_rate >= GATEWAY_HEALTH_THRESHOLDS["DEGRADED_FAILURE_RATE_PCT"]
                or recent_failure_count >= GATEWAY_HEALTH_THRESHOLDS["DEGRADED_RECENT_FAILURES"]
            ):
                current_status = "DEGRADED"
            else:
                current_status = "HEALTHY"

            incident_count = len(inc_list) if inc_list else (1 if current_status != "HEALTHY" else 0)

            result.append({
                "gateway": str(gw_name),
                "current_status": str(current_status),
                "average_latency_ms": avg_latency,
                "average_success_rate": average_success_rate,
                "average_error_rate": failure_rate,
                "failure_rate": failure_rate,
                "total_transactions": total_txns,
                "successful_transactions": success_txns,
                "failed_transactions": failed_txns,
                "recent_failure_count": recent_failure_count,
                "impacted_merchants": impacted_merchants,
                "amount_at_risk": amount_at_risk,
                "incident_count": incident_count,
                "error_dominant": error_dominant
            })

        return result

    def get_failure_intelligence(self) -> List[Dict[str, Any]]:
        payments = self.ds.get_payments()
        failures = self.ds.get_payment_failures()

        merged = pd.merge(payments, failures, on='payment_id', how='inner')
        if merged.empty:
            return []

        merged['date'] = pd.to_datetime(merged['created_at']).dt.strftime('%Y-%m-%d')
        grouped = merged.groupby('failure_category')

        result = []
        for cat_name, group in grouped:
            failure_count = len(group)
            affected_merchant_count = int(group['merchant_id'].nunique())
            total_amount_at_risk = float(round(group['amount_inr'].sum(), 2))
            affected_gateways = group['gateway'].unique().tolist()

            # Trend data over time (daily count)
            daily_counts = group.groupby('date')['payment_id'].count().reset_index()
            daily_counts.columns = ['date', 'count']
            trend_data = daily_counts.to_dict(orient='records')

            result.append({
                "failure_category": str(cat_name),
                "failure_count": failure_count,
                "affected_merchant_count": affected_merchant_count,
                "total_amount_at_risk": total_amount_at_risk,
                "affected_gateways": affected_gateways,
                "trend_data": trend_data
            })

        return result

    def get_merchant_network(self) -> List[Dict[str, Any]]:
        merchants = self.ds.get_merchants()
        payments = self.ds.get_payments()
        recovery = self.ds.get_recovery_attempts()

        result = []
        for _, m_row in merchants.iterrows():
            m_id = m_row['merchant_id']
            m_payments = payments[payments['merchant_id'] == m_id]
            
            tx_count = len(m_payments)
            if tx_count == 0:
                result.append({
                    "merchant_id": m_id,
                    "merchant_name": m_row['merchant_name'],
                    "industry": m_row['industry'],
                    "merchant_segment": m_row['merchant_segment'],
                    "payment_volume": 0.0,
                    "transaction_count": 0,
                    "failure_count": 0,
                    "failure_rate": 0.0,
                    "recovery_rate": 0.0
                })
                continue

            vol = float(round(m_payments['amount_inr'].sum(), 2))
            fail_count = int((m_payments['status'] == 'Failed').sum())
            fail_rate = float(round(fail_count / tx_count * 100, 2))

            m_recovery = recovery[recovery['payment_id'].isin(m_payments['payment_id'])]
            rec_volume = float(m_recovery['recovered_amount_inr'].sum())
            risk_volume = float(m_recovery['risk_amount_inr'].sum())
            tot_risk = rec_volume + risk_volume
            rec_rate = float(round(rec_volume / tot_risk * 100, 2)) if tot_risk > 0 else 0.0

            result.append({
                "merchant_id": m_id,
                "merchant_name": m_row['merchant_name'],
                "industry": m_row['industry'],
                "merchant_segment": m_row['merchant_segment'],
                "payment_volume": vol,
                "transaction_count": tx_count,
                "failure_count": fail_count,
                "failure_rate": fail_rate,
                "recovery_rate": rec_rate
            })

        return result

    def get_recovery_intelligence(self) -> List[Dict[str, Any]]:
        recovery = self.ds.get_recovery_attempts()
        if recovery.empty:
            return []

        grouped = recovery.groupby('strategy')
        result = []

        for strat_name, group in grouped:
            total_attempts = len(group)
            successful_attempts = int((group['attempt_status'] == 'Recovered').sum())
            failed_attempts = int((group['attempt_status'] == 'Failed').sum())
            pending_attempts = int((group['attempt_status'] == 'Pending').sum())
            recovered_amount = float(round(group['recovered_amount_inr'].sum(), 2))
            success_rate = float(round(successful_attempts / total_attempts * 100, 2)) if total_attempts > 0 else 0.0
            avg_predicted_prob = float(round(group['predicted_recovery_probability'].mean(), 4))

            result.append({
                "strategy": str(strat_name),
                "total_attempts": total_attempts,
                "successful_attempts": successful_attempts,
                "failed_attempts": failed_attempts,
                "pending_attempts": pending_attempts,
                "recovered_amount_inr": recovered_amount,
                "success_rate": success_rate,
                "average_predicted_recovery_probability": avg_predicted_prob
            })

        return result
