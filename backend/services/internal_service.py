import pandas as pd
from typing import Dict, Any, List
from services.data_service import get_data_service

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
        gateway_events = self.ds.get_gateway_events()
        if gateway_events.empty:
            return []

        # Get DB active incidents to correlate gateway status
        active_gateways_with_incidents = set()
        try:
            from services.infrastructure_incident_service import get_infrastructure_incident_service
            db_incidents = get_infrastructure_incident_service().get_all_incidents()
            for inc in db_incidents:
                if inc.get("status") == "ACTIVE" and inc.get("gateway"):
                    active_gateways_with_incidents.add(inc.get("gateway").upper())
        except Exception:
            pass

        grouped = gateway_events.groupby('gateway')
        result = []

        for gw_name, group in grouped:
            avg_latency = float(round(group['latency_ms'].mean(), 2))
            avg_success = float(round(group['success_rate'].mean(), 2))
            avg_error = float(round(group['error_rate'].mean(), 2))
            incident_count = int(group['is_incident'].sum())
            
            # Current status from latest event timestamp
            latest_row = group.sort_values('timestamp').iloc[-1]
            current_status = str(latest_row['status'])

            # Override status if active incident logged in SQLite DB
            gw_upper = str(gw_name).upper()
            if any(gw_u in gw_upper for gw_u in active_gateways_with_incidents):
                current_status = "DEGRADED"
                incident_count = max(incident_count, 1)

            result.append({
                "gateway": str(gw_name),
                "average_latency_ms": avg_latency,
                "average_success_rate": avg_success,
                "average_error_rate": avg_error,
                "incident_count": incident_count,
                "current_status": current_status
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
