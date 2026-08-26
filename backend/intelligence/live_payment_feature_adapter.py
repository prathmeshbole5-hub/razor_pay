from typing import Dict, Any, Tuple
from datetime import datetime
import pandas as pd

class LivePaymentFeatureAdapter:
    """
    Feature adapter mapping live Razorpay payment fields into the exact 18 feature columns
    expected by RecoverAI ML pipeline models (RandomForestClassifier).
    Does NOT mutate original historical CSV datasets.
    """

    @staticmethod
    def adapt_live_payment(live_payment: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Maps a live payment record to ML model input features + data quality metadata.
        """
        pm_id = live_payment.get("payment_id", "pay_live_unknown")
        m_id = live_payment.get("merchant_id", "m_1004")
        amt = float(live_payment.get("amount_inr", 500.0))
        status = live_payment.get("status", "failed")
        method = live_payment.get("payment_method", "Card")
        bank = live_payment.get("bank", "Razorpay Gateway")
        err_code = live_payment.get("error_code") or "BAD_REQUEST_ABANDONED"
        err_desc = live_payment.get("error_description") or "Payment authorization failed"

        # Determine failure category
        cat = "User Abandoned"
        if "timeout" in err_desc.lower() or "timeout" in err_code.lower():
            cat = "Network Timeout"
        elif "declined" in err_desc.lower() or "bank" in str(err_code).lower():
            cat = "Bank Declined"
        elif "otp" in err_desc.lower():
            cat = "OTP Failed"

        # Calculate time features
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        is_weekend = 1 if day_of_week in (5, 6) else 0

        # Feature Completeness tracking
        raw_fields = [live_payment.get("amount_inr"), live_payment.get("payment_method"), live_payment.get("bank"), live_payment.get("error_code")]
        valid_count = sum(1 for f in raw_fields if f is not None)
        completeness = round(valid_count / len(raw_fields), 2)

        adapted_features = {
            # Identifiers
            "payment_id": pm_id,
            "merchant_id": m_id,
            
            # Payment Features
            "amount_inr": amt,
            "payment_method": method,
            "gateway": bank,
            "transaction_hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            
            # Failure Features
            "failure_category": cat,
            "error_code": err_code,
            "retryable": True if status == "failed" else False,
            
            # Merchant Historical Features (Defaults for live adapter context)
            "merchant_segment": "Enterprise",
            "industry": "E-Commerce",
            "merchant_historical_tx_count": 120,
            "merchant_historical_failure_rate": 18.5,
            "merchant_historical_recovery_rate": 74.2,
            
            # Gateway Telemetry Features
            "gateway_historical_latency_ms": 185.0,
            "gateway_historical_success_rate": 97.2,
            "gateway_historical_error_rate": 2.8,
            "gateway_historical_incident_count": 0,
            
            # Recovery Context Defaults
            "strategy": "Smart gateway retry",
            "attempt_number": 1,
            "delay_minutes": 10,
            "predicted_recovery_probability": 0.65
        }

        data_quality = {
            "source": live_payment.get("source", "razorpay_test_mode"),
            "prediction_mode": "live_adapted",
            "feature_completeness": completeness,
            "is_live_event": True
        }

        return adapted_features, data_quality
