import os
import hmac
import hashlib
import json
import base64
import random
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
RAZORPAY_ENABLED = os.environ.get("RAZORPAY_ENABLED", "false").lower() in ("true", "1", "yes")

class RazorpayService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RazorpayService, cls).__new__(cls)
        return cls._instance

    def is_enabled(self) -> bool:
        """Returns True if Razorpay integration is explicitly enabled with Key ID"""
        return bool(RAZORPAY_ENABLED and RAZORPAY_KEY_ID)

    def get_key_id(self) -> str:
        """Returns public key ID for client side without exposing secret"""
        return RAZORPAY_KEY_ID or "rzp_test_placeholder"

    def create_order(
        self,
        amount: float,
        currency: str = "INR",
        merchant_id: str = "m_1004",
        receipt: str = "recoverai_demo_order"
    ) -> Dict[str, Any]:
        """
        Creates a Razorpay Test Mode Order.
        If credentials exist and are enabled, calls Razorpay Order API server-to-server.
        If disabled or missing credentials, returns a safe simulated Test Mode Order payload.
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")

        # Amount in paise (integer)
        amount_paise = int(amount if amount >= 100 else amount * 100)

        if self.is_enabled() and RAZORPAY_KEY_SECRET:
            try:
                url = "https://api.razorpay.com/v1/orders"
                payload = {
                    "amount": amount_paise,
                    "currency": currency.upper(),
                    "receipt": receipt,
                    "notes": {
                        "merchant_id": merchant_id,
                        "source": "RecoverAI"
                    }
                }
                data = json.dumps(payload).encode("utf-8")
                
                auth_str = f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}"
                auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
                
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Basic {auth_b64}"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    return {
                        "order_id": resp_data.get("id"),
                        "amount": resp_data.get("amount", amount_paise),
                        "currency": resp_data.get("currency", currency),
                        "key_id": self.get_key_id(),
                        "merchant_id": merchant_id,
                        "status": "created",
                        "mode": "razorpay_live_test"
                    }
            except Exception as e:
                print(f"[RazorpayService] Live API call failed, falling back to safe test mode: {e}")

        # Safe fallback test mode order payload
        mock_order_id = f"order_test_{random.randint(100000, 999999)}"
        return {
            "order_id": mock_order_id,
            "amount": amount_paise,
            "currency": currency.upper(),
            "key_id": self.get_key_id(),
            "merchant_id": merchant_id,
            "status": "created",
            "mode": "test_mock"
        }

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """
        Verifies Razorpay payment signature server-side using HMAC-SHA256.
        Formula: HMAC-SHA256(order_id + '|' + payment_id, secret)
        """
        if not signature or not order_id or not payment_id:
            return False

        secret = RAZORPAY_KEY_SECRET
        if not secret:
            # In test/disabled mode without secret, check basic test format
            return signature.startswith("sig_valid_") or signature.startswith("sig_test_")

        try:
            msg = f"{order_id}|{payment_id}".encode("utf-8")
            generated = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
            return hmac.compare_digest(generated, signature)
        except Exception as e:
            print(f"[RazorpayService] Signature verification error: {e}")
            return False

    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature_header: str
    ) -> bool:
        """
        Verifies Razorpay Webhook signature server-side.
        Formula: HMAC-SHA256(raw_body_bytes, webhook_secret)
        """
        if not signature_header or not body_bytes:
            return False

        secret = RAZORPAY_WEBHOOK_SECRET
        if not secret:
            # Test fallback if secret not set
            return signature_header.startswith("whsec_test_") or signature_header == "test_signature"

        try:
            generated = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
            return hmac.compare_digest(generated, signature_header)
        except Exception as e:
            print(f"[RazorpayService] Webhook signature verification error: {e}")
            return False

def get_razorpay_service() -> RazorpayService:
    return RazorpayService()
