import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from services.data_service import get_data_service
from intelligence.intelligence_data_service import get_intelligence_data_service

class RootCauseService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RootCauseService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.data_service = get_data_service()
        self.intelligence_service = get_intelligence_data_service()

    def analyze_root_cause(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Performs deterministic root cause analysis for a payment based on failure codes,
        gateway telemetry, retryability, and historical merchant patterns.
        Distinguishes between captured/successful payments and failed payments.
        """
        # 1. Check if this is a live payment record
        from services.live_payment_service import get_live_payment_service
        lps = get_live_payment_service()
        live_rec = lps.get_live_payment(payment_id, "m_1004")
        if not live_rec:
            # Fallback query without merchant constraint
            from database import SessionLocal, LivePaymentModel
            db = SessionLocal()
            try:
                rec_model = db.query(LivePaymentModel).filter(
                    (LivePaymentModel.payment_id == payment_id) |
                    (LivePaymentModel.razorpay_payment_id == payment_id) |
                    (LivePaymentModel.order_id == payment_id)
                ).first()
                if rec_model:
                    live_rec = lps._model_to_dict(rec_model, db)
            finally:
                db.close()

        row = None
        if live_rec:
            status = str(live_rec.get("status", "")).lower()
            if status in ["captured", "verified", "successful", "success"]:
                return {
                    "payment_id": payment_id,
                    "primary_root_cause": {
                        "category": "Captured",
                        "title": "Successful Payment Authorization & Settlement",
                        "reason": "Transaction was authorized and captured successfully via Razorpay Payment Gateway with zero authorization drop-off.",
                        "confidence": 0.98
                    },
                    "contributing_factors": [
                        {
                            "factor": "Successful 3DS Authorization",
                            "impact": "Positive",
                            "detail": "Customer completed 2FA authentication and bank approved authorization."
                        }
                    ],
                    "evidence": {
                        "failure_category": "Captured",
                        "error_code": live_rec.get("error_code") or "SUCCESS",
                        "gateway": live_rec.get("bank") or "Razorpay Gateway",
                        "payment_method": live_rec.get("payment_method") or "Card",
                        "retryable": False
                    }
                }
            
            # Live payment that failed or is created
            error_code = str(live_rec.get("error_code") or "BAD_REQUEST_ABANDONED")
            error_desc = str(live_rec.get("error_description") or "Payment authorization failed")
            err_code_lower = error_code.lower()
            err_desc_lower = error_desc.lower()
            
            if "international" in err_code_lower or "international" in err_desc_lower or "card_not_supported" in err_code_lower or "not_allowed" in err_code_lower or "restriction" in err_desc_lower:
                fail_cat = "Payment Method Restriction"
            elif "timeout" in err_desc_lower or "timeout" in err_code_lower:
                fail_cat = "Network Timeout"
            elif "declined" in err_desc_lower or "bank" in err_code_lower or "balance" in err_desc_lower or "insufficient" in err_code_lower:
                fail_cat = "Bank Declined"
            elif "otp" in err_desc_lower or "3ds" in err_code_lower:
                fail_cat = "OTP Failed"
            elif "abandon" in err_code_lower or "abandon" in err_desc_lower or "cancel" in err_desc_lower or "closed" in err_desc_lower:
                fail_cat = "User Abandoned"
            else:
                fail_cat = "Payment Authorization Failure"

            row = {
                "payment_id": payment_id,
                "failure_category": fail_cat,
                "error_code": error_code,
                "gateway": live_rec.get("bank") or "Razorpay Gateway",
                "payment_method": live_rec.get("payment_method") or "Card",
                "retryable": True,
                "gateway_historical_latency_ms": 180.0,
                "gateway_historical_error_rate": 2.5,
                "gateway_historical_incident_count": 0,
                "merchant_historical_failure_rate": 5.0
            }

        if not row:
            derived_df = self.intelligence_service.get_intelligence_dataset()
            match = derived_df[derived_df['payment_id'] == payment_id]
            if match.empty:
                return None
            row = match.iloc[0].to_dict()

        failure_category = str(row.get('failure_category', 'Unknown'))
        error_code = str(row.get('error_code', 'UNKNOWN_ERROR'))
        gateway = str(row.get('gateway', 'Unknown'))
        payment_method = str(row.get('payment_method', 'Unknown'))
        retryable = bool(row.get('retryable', True))
        
        gw_latency = float(row.get('gateway_historical_latency_ms', 180.0))
        gw_error_rate = float(row.get('gateway_historical_error_rate', 2.5))
        gw_incidents = int(row.get('gateway_historical_incident_count', 0))
        merchant_fail_rate = float(row.get('merchant_historical_failure_rate', 0.0))

        # Deterministic Root Cause Mapping & Explanation
        if failure_category == 'Payment Method Restriction' or 'INTERNATIONAL' in error_code.upper() or 'CARD_NOT_SUPPORTED' in error_code.upper():
            primary_cause = "Payment Method / Card Restriction"
            reason = f"The selected card is not supported for this transaction in the current Razorpay Test Mode configuration. ({error_desc})"
            base_confidence = 0.96
        elif failure_category == 'User Abandoned' or 'ABANDONED' in error_code:
            primary_cause = "Customer Checkout Session Drop-off"
            reason = "Customer abandoned payment verification or closed browser tab before completing 3DS authorization."
            base_confidence = 0.88
        elif failure_category == 'Bank Declined' or 'INSUFFICIENT' in error_code or 'DECLINED' in error_code:
            primary_cause = "Issuing Bank Account / Authorization Decline"
            reason = "Issuing bank rejected authorization request due to insufficient balance, card limit, or bank security policy."
            base_confidence = 0.92
        elif failure_category == 'Network Timeout' or 'TIMEOUT' in error_code:
            primary_cause = "Bank Gateway Network Handshake Timeout"
            reason = f"Network socket connection to {gateway} timed out before receiving HTTP 200 authorization response."
            base_confidence = 0.90
        elif failure_category == 'Gateway Error' or 'INTERNAL_ERROR' in error_code:
            primary_cause = "Partner Gateway Server Degraded Performance"
            reason = f"Routing node for {gateway} returned internal error response during payment processing."
            base_confidence = 0.89
        elif failure_category == 'OTP Failed' or 'OTP' in error_code:
            primary_cause = "Two-Factor Authentication (2FA/OTP) Failure"
            reason = "Customer entered an invalid OTP code or 3DS verification window expired."
            base_confidence = 0.94
        else:
            primary_cause = f"Payment Method Failure ({error_code})"
            reason = f"Payment failed with error code '{error_code}': {error_desc}."
            base_confidence = 0.85

        # Weighted Confidence Adjustments
        confidence_adj = 0.0
        if gw_incidents > 0:
            confidence_adj += 0.04
        if gw_error_rate > 3.0:
            confidence_adj += 0.03
        if retryable:
            confidence_adj += 0.01

        final_confidence = float(round(min(base_confidence + confidence_adj, 0.98), 4))

        # Contributing Factors
        factors: List[Dict[str, Any]] = []

        if gw_error_rate > 3.0 or gw_incidents > 0:
            factors.append({
                "factor": f"{gateway} Gateway Elevated Error Spike",
                "impact": "High" if gw_incidents > 0 else "Medium",
                "detail": f"Gateway error rate is at {gw_error_rate}% with {gw_incidents} active incidents."
            })

        if gw_latency > 250.0:
            factors.append({
                "factor": f"{gateway} High Network Latency",
                "impact": "Medium",
                "detail": f"Average response latency of {gw_latency}ms recorded on routing node."
            })

        if merchant_fail_rate > 50.0:
            factors.append({
                "factor": "Merchant Integration Failure Baseline",
                "impact": "Medium",
                "detail": f"Merchant has elevated historical failure rate of {merchant_fail_rate}%."
            })

        if retryable:
            factors.append({
                "factor": "Transaction Retryability State",
                "impact": "Low",
                "detail": "Error code indicates payment is safe for automated retry attempt."
            })

        if not factors:
            factors.append({
                "factor": "Standard Processing Variance",
                "impact": "Low",
                "detail": "No anomalous infrastructure degradation detected."
            })

        return {
            "payment_id": payment_id,
            "primary_root_cause": {
                "category": failure_category,
                "title": primary_cause,
                "reason": reason,
                "confidence": final_confidence
            },
            "contributing_factors": factors,
            "evidence": {
                "failure_category": failure_category,
                "error_code": error_code,
                "gateway": gateway,
                "payment_method": payment_method,
                "gateway_error_rate": gw_error_rate,
                "gateway_latency_ms": gw_latency,
                "merchant_historical_failure_rate": merchant_fail_rate,
                "retryable": retryable
            }
        }

def get_root_cause_service() -> RootCauseService:
    return RootCauseService()
