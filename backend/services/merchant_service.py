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

        # 1. Fetch live payment records & recovery actions from SQLite DB
        live_records = []
        recovery_actions = []
        try:
            from database import SessionLocal, LivePaymentModel, RecoveryActionModel
            db = SessionLocal()
            try:
                live_records = db.query(LivePaymentModel).filter_by(merchant_id=merchant_id).all()
                recovery_actions = db.query(RecoveryActionModel).filter_by(merchant_id=merchant_id).all()
            finally:
                db.close()
        except Exception as db_err:
            print(f"[MerchantService] DB query notice: {db_err}")

        # 2. Calculate metrics from SQLite single source of truth
        total_payments = len(live_records)
        failed_list = [p for p in live_records if str(p.status or "").lower() == "failed"]
        success_list = [p for p in live_records if str(p.status or "").lower() in ("captured", "verified", "successful", "success")]
        
        failed_payments = len(failed_list)
        successful_payments = len(success_list)
        payment_volume = float(sum(p.amount or 0.0 for p in live_records))
        revenue_at_risk = float(sum(p.amount or 0.0 for p in failed_list))
        revenue_recovered = float(sum(p.amount or 0.0 for p in success_list))

        # Track executed recovery actions
        action_recovered_ids = set()
        for act in recovery_actions:
            if act.status in ("executed", "completed") and act.action_type in ("smart_retry", "otp_reminder", "payment_link"):
                action_recovered_ids.add(act.payment_id)

        action_recovered_sum = 0.0
        for p in failed_list:
            if p.payment_id in action_recovered_ids or p.razorpay_payment_id in action_recovered_ids:
                action_recovered_sum += float(p.amount or 0.0)

        if action_recovered_sum > 0:
            revenue_recovered += action_recovered_sum
            revenue_at_risk = max(0.0, revenue_at_risk - action_recovered_sum)

        total_risk = revenue_at_risk + revenue_recovered
        recovery_rate = round((revenue_recovered / total_risk * 100), 2) if total_risk > 0 else 0.0
        active_cases = max(0, failed_payments - len(action_recovered_ids))

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

        # Fetch live failed payments from SQLite
        live_failed = []
        try:
            from database import SessionLocal, LivePaymentModel
            db = SessionLocal()
            try:
                live_recs = db.query(LivePaymentModel).filter_by(merchant_id=merchant_id).all()
                live_failed = [p for p in live_recs if str(p.status or "").lower() == "failed"]
            finally:
                db.close()
        except Exception as db_err:
            print(f"[MerchantService] DB failed payments notice: {db_err}")

        result = []
        for p in live_failed:
            created_str = p.created_at.isoformat() if hasattr(p.created_at, 'isoformat') else str(p.created_at or "")
            result.append({
                "payment_id": str(p.payment_id),
                "merchant_id": str(p.merchant_id),
                "amount_inr": float(p.amount or 0.0),
                "payment_method": str(p.payment_method or "Card"),
                "gateway": str(p.bank or "Razorpay Gateway"),
                "created_at": created_str,
                "failure_category": str(p.error_description or p.error_code or "Payment Authorization Failed"),
                "error_code": str(p.error_code or "BAD_REQUEST"),
                "retryable": True
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
