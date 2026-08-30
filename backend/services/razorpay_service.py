import os
import hmac
import hashlib
import json
import base64
import urllib.request
import urllib.error
from typing import Dict, Any

from dotenv import load_dotenv

# Load backend/.env
load_dotenv()


# ============================================================
# RAZORPAY CONFIGURATION
# ============================================================

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()

RAZORPAY_ENABLED = (
    os.getenv("RAZORPAY_ENABLED", "false").strip().lower()
    in ("true", "1", "yes")
)


# ============================================================
# RAZORPAY SERVICE
# ============================================================

class RazorpayService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RazorpayService, cls).__new__(cls)

        return cls._instance

    # ========================================================
    # CONFIG
    # ========================================================

    def is_enabled(self) -> bool:
        """
        Returns True only when Razorpay Test Mode credentials
        are configured and Razorpay integration is enabled.
        """

        return bool(
            RAZORPAY_ENABLED
            and RAZORPAY_KEY_ID
            and RAZORPAY_KEY_SECRET
        )

    def get_key_id(self) -> str:
        """
        Returns the PUBLIC Razorpay Key ID.

        Never expose the secret key to the frontend.
        """

        return RAZORPAY_KEY_ID

    # ========================================================
    # CREATE RAZORPAY ORDER
    # ========================================================

    def create_order(
        self,
        amount: float,
        currency: str = "INR",
        merchant_id: str = "m_1004",
        receipt: str = "recoverai_demo_order",
    ) -> Dict[str, Any]:
        """
        Create a REAL Razorpay Test Mode order.

        IMPORTANT:
        Razorpay expects amount in the smallest currency unit.

        Example:

            ₹1    -> 100 paise
            ₹100  -> 10000 paise
            ₹200  -> 20000 paise
        """

        # ----------------------------------------------------
        # Validate amount
        # ----------------------------------------------------

        if amount <= 0:
            raise ValueError("Amount must be greater than zero")

        # ----------------------------------------------------
        # Validate credentials
        # ----------------------------------------------------

        if not RAZORPAY_ENABLED:
            raise RuntimeError(
                "Razorpay is disabled. Set RAZORPAY_ENABLED=true in .env"
            )

        if not RAZORPAY_KEY_ID:
            raise RuntimeError(
                "RAZORPAY_KEY_ID is missing from .env"
            )

        if not RAZORPAY_KEY_SECRET:
            raise RuntimeError(
                "RAZORPAY_KEY_SECRET is missing from .env"
            )

        # ----------------------------------------------------
        # Convert INR -> paise
        # ----------------------------------------------------

        amount_paise = int(round(amount * 100))

        # ----------------------------------------------------
        # Prepare Razorpay API request
        # ----------------------------------------------------

        url = "https://api.razorpay.com/v1/orders"

        payload = {
            "amount": amount_paise,
            "currency": currency.upper(),
            "receipt": receipt,
            "notes": {
                "merchant_id": merchant_id,
                "source": "RecoverAI",
            },
        }

        data = json.dumps(payload).encode("utf-8")

        # ----------------------------------------------------
        # Basic Authentication
        #
        # username = Razorpay Key ID
        # password = Razorpay Key Secret
        # ----------------------------------------------------

        credentials = f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}"

        auth_b64 = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Basic {auth_b64}",
            },
            method="POST",
        )

        # ----------------------------------------------------
        # Call Razorpay
        # ----------------------------------------------------

        try:

            with urllib.request.urlopen(
                request,
                timeout=15,
            ) as response:

                response_body = response.read().decode("utf-8")

                razorpay_response = json.loads(response_body)

        except urllib.error.HTTPError as error:

            error_body = ""

            try:
                error_body = error.read().decode("utf-8")
            except Exception:
                pass

            print(
                "\n=================================================="
            )
            print("[RazorpayService] RAZORPAY API ERROR")
            print("HTTP Status :", error.code)
            print("Response    :", error_body)
            print(
                "==================================================\n"
            )

            if error.code == 401:
                raise RuntimeError(
                    "Razorpay returned 401 Unauthorized. "
                    "Check RAZORPAY_KEY_ID and "
                    "RAZORPAY_KEY_SECRET in backend/.env. "
                    "Both keys must belong to the same Razorpay "
                    "Test Mode account."
                )

            raise RuntimeError(
                f"Razorpay API error {error.code}: {error_body}"
            )

        except urllib.error.URLError as error:

            raise RuntimeError(
                f"Could not connect to Razorpay: {error.reason}"
            )

        except json.JSONDecodeError:

            raise RuntimeError(
                "Razorpay returned an invalid JSON response."
            )

        # ----------------------------------------------------
        # Validate Razorpay response
        # ----------------------------------------------------

        razorpay_order_id = razorpay_response.get("id")

        if not razorpay_order_id:

            raise RuntimeError(
                f"Razorpay did not return an order ID: "
                f"{razorpay_response}"
            )

        # A real Razorpay order should look like:
        #
        # order_XXXXXXXXXXXXXX
        #

        if not razorpay_order_id.startswith("order_"):

            raise RuntimeError(
                f"Invalid Razorpay order ID returned: "
                f"{razorpay_order_id}"
            )

        # ----------------------------------------------------
        # Return REAL Razorpay order
        # ----------------------------------------------------

        return {
            "order_id": razorpay_order_id,
            "amount": razorpay_response.get(
                "amount",
                amount_paise,
            ),
            "currency": razorpay_response.get(
                "currency",
                currency.upper(),
            ),
            "key_id": RAZORPAY_KEY_ID,
            "merchant_id": merchant_id,
            "status": "created",
            "mode": "razorpay_test",
        }

    # ========================================================
    # VERIFY PAYMENT SIGNATURE
    # ========================================================

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """
        Verify Razorpay payment signature.

        Formula:

        HMAC-SHA256(
            razorpay_order_id + "|" + razorpay_payment_id,
            RAZORPAY_KEY_SECRET
        )
        """

        if not order_id:
            return False

        if not payment_id:
            return False

        if not signature:
            return False

        if not RAZORPAY_KEY_SECRET:
            print(
                "[RazorpayService] "
                "Cannot verify payment: secret key missing."
            )
            return False

        try:

            message = (
                f"{order_id}|{payment_id}"
            ).encode("utf-8")

            generated_signature = hmac.new(
                RAZORPAY_KEY_SECRET.encode("utf-8"),
                message,
                hashlib.sha256,
            ).hexdigest()

            is_valid = hmac.compare_digest(
                generated_signature,
                signature,
            )

            if is_valid:

                print(
                    "[RazorpayService] "
                    "Payment signature verified successfully."
                )

            else:

                print(
                    "[RazorpayService] "
                    "Payment signature verification FAILED."
                )

            return is_valid

        except Exception as error:

            print(
                f"[RazorpayService] "
                f"Signature verification error: {error}"
            )

            return False

    # ========================================================
    # VERIFY WEBHOOK SIGNATURE
    # ========================================================

    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature_header: str,
    ) -> bool:
        """
        Verify Razorpay webhook signature.

        Formula:

        HMAC-SHA256(
            raw_request_body,
            RAZORPAY_WEBHOOK_SECRET
        )
        """

        if not body_bytes:
            return False

        if not signature_header:
            return False

        if not RAZORPAY_WEBHOOK_SECRET:
            print(
                "[RazorpayService] "
                "Webhook secret is not configured."
            )
            return False

        try:

            generated_signature = hmac.new(
                RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
                body_bytes,
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(
                generated_signature,
                signature_header,
            )

        except Exception as error:

            print(
                "[RazorpayService] "
                f"Webhook verification error: {error}"
            )

            return False


# ============================================================
# SINGLETON ACCESSOR
# ============================================================

def get_razorpay_service() -> RazorpayService:
    return RazorpayService()