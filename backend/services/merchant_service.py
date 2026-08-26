import pandas as pd
from typing import Optional, Dict, Any, List
from services.data_service import get_data_service

class MerchantService:
    def __init__(self):
        self.ds = get_data_service()

    def _validate_merchant(self, merchant_id: str) -> bool:
        merchants = self.ds.get_merchants()
        return not merchants[merchants['merchant_id'] == merchant_id].empty

    def get_dashboard(self, merchant_id: str) -> Optional[Dict[str, Any]]:
        if not self._validate_merchant(merchant_id):
            return None

        payments = self.ds.get_payments()
        merchant_payments = payments[payments['merchant_id'] == merchant_id]
        
        if merchant_payments.empty:
            return {
                "merchant_id": merchant_id,
                "total_payments": 0,
                "successful_payments": 0,
                "failed_payments": 0,
                "payment_volume": 0.0,
                "revenue_at_risk": 0.0,
                "revenue_recovered": 0.0,
                "recovery_rate": 0.0,
                "active_recovery_cases": 0
            }

        total_payments = len(merchant_payments)
        successful_payments = int((merchant_payments['status'] == 'Success').sum())
        failed_payments = int((merchant_payments['status'] == 'Failed').sum())
        payment_volume = float(merchant_payments['amount_inr'].sum())

        payment_ids = merchant_payments['payment_id']
        recovery_attempts = self.ds.get_recovery_attempts()
        m_recovery = recovery_attempts[recovery_attempts['payment_id'].isin(payment_ids)]

        revenue_at_risk = float(m_recovery['risk_amount_inr'].sum())
        revenue_recovered = float(m_recovery['recovered_amount_inr'].sum())

        total_risk = revenue_at_risk + revenue_recovered
        recovery_rate = round((revenue_recovered / total_risk * 100), 2) if total_risk > 0 else 0.0
        active_cases = int((m_recovery['attempt_status'] == 'Pending').sum())

        return {
            "merchant_id": merchant_id,
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "payment_volume": round(payment_volume, 2),
            "revenue_at_risk": round(revenue_at_risk, 2),
            "revenue_recovered": round(revenue_recovered, 2),
            "recovery_rate": recovery_rate,
            "active_recovery_cases": active_cases
        }

    def get_failed_payments(self, merchant_id: str) -> Optional[List[Dict[str, Any]]]:
        if not self._validate_merchant(merchant_id):
            return None

        payments = self.ds.get_payments()
        m_payments = payments[(payments['merchant_id'] == merchant_id) & (payments['status'] == 'Failed')]

        if m_payments.empty:
            return []

        failures = self.ds.get_payment_failures()
        merged = pd.merge(m_payments, failures, on='payment_id', how='inner')

        result = []
        for _, row in merged.iterrows():
            result.append({
                "payment_id": str(row['payment_id']),
                "amount_inr": float(row['amount_inr']),
                "payment_method": str(row['payment_method']),
                "gateway": str(row['gateway']),
                "created_at": str(row['created_at']),
                "failure_category": str(row['failure_category']),
                "error_code": str(row['error_code']),
                "retryable": bool(row['retryable'])
            })
        return result

    def get_recovery_cases(self, merchant_id: str) -> Optional[List[Dict[str, Any]]]:
        if not self._validate_merchant(merchant_id):
            return None

        payments = self.ds.get_payments()
        m_payments = payments[payments['merchant_id'] == merchant_id]
        if m_payments.empty:
            return []

        failures = self.ds.get_payment_failures()
        recovery = self.ds.get_recovery_attempts()

        merged = pd.merge(m_payments, failures, on='payment_id', how='inner')
        merged = pd.merge(merged, recovery, on='payment_id', how='inner')

        result = []
        for _, row in merged.iterrows():
            result.append({
                "payment_id": str(row['payment_id']),
                "amount": float(row['amount_inr']),
                "amount_inr": float(row['amount_inr']),
                "failure_category": str(row['failure_category']),
                "strategy": str(row['strategy']),
                "attempt_number": int(row['attempt_number']),
                "delay_minutes": int(row['delay_minutes']),
                "attempt_status": str(row['attempt_status']),
                "predicted_recovery_probability": float(row['predicted_recovery_probability']),
                "resolved_at": str(row['resolved_at']) if pd.notnull(row.get('resolved_at')) else None
            })
        return result

    def get_analytics(self, merchant_id: str) -> Optional[Dict[str, Any]]:
        if not self._validate_merchant(merchant_id):
            return None

        payments = self.ds.get_payments()
        m_payments = payments[payments['merchant_id'] == merchant_id]

        if m_payments.empty:
            return {
                "failures_by_reason": [],
                "failures_by_payment_method": [],
                "payment_trend": [],
                "recovery_trend": [],
                "recovery_performance_by_strategy": []
            }

        failures = self.ds.get_payment_failures()
        recovery = self.ds.get_recovery_attempts()

        # All initial failure events for this merchant
        m_failures = pd.merge(m_payments, failures, on='payment_id', how='inner')
        m_recovery = pd.merge(m_payments, recovery, on='payment_id', how='inner')

        # Failures by reason
        reason_counts = m_failures['failure_category'].value_counts().reset_index()
        reason_counts.columns = ['reason', 'count']
        failures_by_reason = reason_counts.to_dict(orient='records')

        # Failures by payment method
        method_counts = m_failures['payment_method'].value_counts().reset_index()
        method_counts.columns = ['method', 'count']
        failures_by_payment_method = method_counts.to_dict(orient='records')

        # Payment trend over time (daily)
        m_payments_copy = m_payments.copy()
        m_payments_copy['date'] = pd.to_datetime(m_payments_copy['created_at']).dt.strftime('%Y-%m-%d')
        daily_payments = m_payments_copy.groupby('date').agg(
            total_volume=('amount_inr', 'sum'),
            total_count=('payment_id', 'count')
        ).reset_index()
        daily_payments['total_volume'] = daily_payments['total_volume'].round(2)
        payment_trend = daily_payments.to_dict(orient='records')

        # Recovery trend over time
        m_rec_copy = m_recovery.copy()
        m_rec_copy['date'] = pd.to_datetime(m_rec_copy['created_at']).dt.strftime('%Y-%m-%d')
        daily_recovery = m_rec_copy.groupby('date').agg(
            recovered_volume=('recovered_amount_inr', 'sum'),
            recovered_count=('attempt_status', lambda x: (x == 'Recovered').sum())
        ).reset_index()
        daily_recovery['recovered_volume'] = daily_recovery['recovered_volume'].round(2)
        recovery_trend = daily_recovery.to_dict(orient='records')

        # Performance by strategy
        strat_perf = m_recovery.groupby('strategy').agg(
            total_attempts=('attempt_id', 'count'),
            successful_attempts=('attempt_status', lambda x: (x == 'Recovered').sum()),
            recovered_amount=('recovered_amount_inr', 'sum')
        ).reset_index()
        strat_perf['recovered_amount'] = strat_perf['recovered_amount'].round(2)
        strat_perf['success_rate'] = strat_perf.apply(
            lambda r: round(r['successful_attempts'] / r['total_attempts'] * 100, 2) if r['total_attempts'] > 0 else 0.0,
            axis=1
        )
        recovery_performance_by_strategy = strat_perf.to_dict(orient='records')

        return {
            "failures_by_reason": failures_by_reason,
            "failures_by_payment_method": failures_by_payment_method,
            "payment_trend": payment_trend,
            "recovery_trend": recovery_trend,
            "recovery_performance_by_strategy": recovery_performance_by_strategy
        }
