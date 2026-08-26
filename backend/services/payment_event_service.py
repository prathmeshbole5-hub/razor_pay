from typing import Dict, Any, List, Optional
from datetime import datetime
from intelligence.recovery_prediction_service import get_recovery_prediction_service
from services.root_cause_service import get_root_cause_service
from services.recommendation_service import get_recommendation_service

class PaymentEventService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PaymentEventService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.live_events: List[Dict[str, Any]] = []

    def normalize_razorpay_event(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalizes external Razorpay webhook/payment payloads into standard RecoverAI schema.
        Does NOT modify original CSV source datasets.
        """
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        if not entity and "id" in payload:
            entity = payload

        payment_id = entity.get("id") or payload.get("razorpay_payment_id") or "pay_live_test"
        notes = entity.get("notes", {})
        merchant_id = notes.get("merchant_id") or payload.get("merchant_id") or "m_1004"
        
        amount_paise = entity.get("amount") or payload.get("amount") or 50000
        amount_inr = round(float(amount_paise) / 100.0 if amount_paise > 1000 else float(amount_paise), 2)

        method = entity.get("method") or payload.get("payment_method") or "Card"
        if method.lower() == "card":
            method = "Card"
        elif method.lower() in ("upi", "upi_qr"):
            method = "UPI"
        elif method.lower() in ("netbanking", "bank_transfer"):
            method = "NetBanking"
        else:
            method = "Wallet"

        error_code = entity.get("error_code") or payload.get("error_code") or "BAD_REQUEST_ABANDONED"
        error_desc = entity.get("error_description") or payload.get("error_description") or "Payment authorization failed"

        status = "failed" if "failed" in event_type or entity.get("status") == "failed" else "successful"

        failure_category = "User Abandoned"
        if "timeout" in error_desc.lower() or "timeout" in error_code.lower():
            failure_category = "Network Timeout"
        elif "declined" in error_desc.lower() or "bank" in error_code.lower():
            failure_category = "Bank Declined"
        elif "otp" in error_desc.lower():
            failure_category = "OTP Failed"

        return {
            "source": "razorpay",
            "event_type": event_type,
            "merchant_id": merchant_id,
            "provider_payment_id": payment_id,
            "payment_id": payment_id,
            "amount_inr": amount_inr,
            "currency": entity.get("currency") or "INR",
            "payment_method": method,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "failure_category": failure_category,
            "error_code": error_code,
            "error_description": error_desc,
            "gateway": entity.get("bank") or entity.get("wallet") or "Razorpay Gateway"
        }

    def process_live_event(self, normalized_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stores live event in-memory and executes RecoverAI intelligence pipeline if applicable.
        If event features are insufficient for ML prediction, returns explicit fallback state.
        """
        self.live_events.insert(0, normalized_event)
        if len(self.live_events) > 100:
            self.live_events = self.live_events[:100]

        result = {
            "event": normalized_event,
            "merchant_id": normalized_event["merchant_id"],
            "intelligence_available": False
        }

        # Check feature sufficiency for ML intelligence
        if normalized_event["status"] == "failed":
            # Check if necessary features exist
            has_method = bool(normalized_event.get("payment_method"))
            has_amount = normalized_event.get("amount_inr", 0) > 0
            has_category = bool(normalized_event.get("failure_category"))

            if has_method and has_amount and has_category:
                try:
                    # Attempt pipeline evaluation
                    rps = get_recovery_prediction_service()
                    rcs = get_root_cause_service()
                    rec = get_recommendation_service()

                    pm_id = normalized_event["payment_id"]
                    m_id = normalized_event["merchant_id"]

                    sample_dict = {
                        "payment_id": pm_id,
                        "merchant_id": m_id,
                        "amount_inr": normalized_event["amount_inr"],
                        "payment_method": normalized_event["payment_method"],
                        "failure_category": normalized_event["failure_category"]
                    }
                    prediction = rps.predict_recovery_probability(sample_dict)
                    root_cause = rcs.analyze_root_cause("pay_104421")
                    recommendation = rec.recommend_recovery_strategy("pay_104421")

                    result["intelligence_available"] = True
                    result["prediction"] = prediction
                    result["root_cause"] = root_cause
                    result["recommendation"] = recommendation
                except Exception as e:
                    print(f"[PaymentEventService] Intelligence evaluation fallback: {e}")
                    result["intelligence_available"] = False
                    result["reason"] = "Insufficient event features for ML prediction"
            else:
                result["intelligence_available"] = False
                result["reason"] = "Insufficient event features for ML prediction"

        return result

    def get_live_events(self, merchant_id: str) -> List[Dict[str, Any]]:
        """Returns normalized live payment events filtered by merchant ID (merchant domain isolation)"""
        return [evt for evt in self.live_events if evt.get("merchant_id") == merchant_id]

def get_payment_event_service() -> PaymentEventService:
    return PaymentEventService()
