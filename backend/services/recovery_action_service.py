import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from database import SessionLocal, RecoveryActionModel, PaymentEventModel, LivePaymentModel
from services.live_payment_service import get_live_payment_service

SUPPORTED_ACTIONS = {
    "otp_reminder": "OTP reminder notification dispatched to customer device",
    "smart_retry": "Smart automated gateway retry scheduled with optimal cool-down interval",
    "payment_link": "Instant SMS & WhatsApp recovery payment link generated and dispatched",
    "retry_later": "Cool-down period initiated before auto-retry attempt",
    "manual_follow_up": "Task assigned to merchant support team for manual outreach"
}

class RecoveryActionService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecoveryActionService, cls).__new__(cls)
        return cls._instance

    def execute_recovery_action(
        self,
        payment_id: str,
        merchant_id: str,
        action_type: str
    ) -> Dict[str, Any]:
        """
        Executes a recovery action for a given payment after enforcing merchant domain isolation.
        Prevents duplicate execution of the same active action.
        """
        if action_type not in SUPPORTED_ACTIONS:
            raise ValueError(f"Unsupported recovery action type '{action_type}'. Supported: {list(SUPPORTED_ACTIONS.keys())}")

        # 1. Verify payment belongs to merchant
        lps = get_live_payment_service()
        live_payment = lps.get_live_payment(payment_id, merchant_id)
        if not live_payment:
            raise KeyError(f"Live payment '{payment_id}' not found for merchant '{merchant_id}'.")

        db = SessionLocal()
        try:
            # 2. Check for duplicate active action execution
            existing_action = db.query(RecoveryActionModel).filter(
                RecoveryActionModel.payment_id == live_payment["payment_id"],
                RecoveryActionModel.action_type == action_type,
                RecoveryActionModel.status == "executed"
            ).first()

            if existing_action:
                raise ValueError(f"Recovery action '{action_type}' was already executed for payment '{payment_id}'. Duplicate action prevented.")

            # 3. Create recovery action record
            action_desc = SUPPORTED_ACTIONS[action_type]
            now = datetime.utcnow()
            
            action_rec = RecoveryActionModel(
                payment_id=live_payment["payment_id"],
                merchant_id=merchant_id,
                action_type=action_type,
                status="executed",
                execution_result=json.dumps({"detail": action_desc, "triggered_by": "merchant_portal"}),
                created_at=now,
                completed_at=now
            )
            db.add(action_rec)

            formatted_action_name = action_type.replace('_', ' ').strip()
            event_msg = f"{formatted_action_name.title()} recovery action executed successfully."
            if formatted_action_name.lower() == "otp reminder":
                event_msg = "OTP reminder recovery action executed successfully."

            # 4. Create payment event
            evt = PaymentEventModel(
                payment_id=live_payment["payment_id"],
                merchant_id=merchant_id,
                event_type="RECOVERY_ACTION_EXECUTED",
                event_description=event_msg,
                metadata_json=json.dumps({"action": action_type, "status": "executed", "detail": action_desc}),
                created_at=now
            )
            db.add(evt)

            db.commit()
            db.refresh(action_rec)

            return {
                "payment_id": live_payment["payment_id"],
                "merchant_id": merchant_id,
                "action": action_type,
                "status": "executed",
                "message": event_msg,
                "action_id": str(action_rec.id),
                "executed_at": action_rec.created_at.isoformat()
            }
        finally:
            db.close()

    def get_payment_actions(self, payment_id: str, merchant_id: str) -> List[Dict[str, Any]]:
        """
        Enforces merchant domain isolation. Returns all executed recovery actions for payment.
        """
        lps = get_live_payment_service()
        live_payment = lps.get_live_payment(payment_id, merchant_id)
        if not live_payment:
            raise KeyError(f"Live payment '{payment_id}' not found for merchant '{merchant_id}'.")

        db = SessionLocal()
        try:
            records = db.query(RecoveryActionModel).filter_by(
                payment_id=live_payment["payment_id"],
                merchant_id=merchant_id
            ).order_by(RecoveryActionModel.created_at.desc()).all()

            return [
                {
                    "action_id": str(r.id),
                    "payment_id": r.payment_id,
                    "merchant_id": r.merchant_id,
                    "action_type": r.action_type,
                    "status": r.status,
                    "execution_result": json.loads(r.execution_result) if r.execution_result else None,
                    "created_at": r.created_at.isoformat() if isinstance(r.created_at, datetime) else str(r.created_at)
                }
                for r in records
            ]
        finally:
            db.close()

    def get_payment_timeline(self, payment_id: str, merchant_id: str) -> List[Dict[str, Any]]:
        """
        Enforces merchant domain isolation. Returns chronologically sorted payment event timeline.
        """
        lps = get_live_payment_service()
        live_payment = lps.get_live_payment(payment_id, merchant_id)
        if not live_payment:
            raise KeyError(f"Live payment '{payment_id}' not found for merchant '{merchant_id}'.")

        db = SessionLocal()
        try:
            records = db.query(PaymentEventModel).filter_by(
                payment_id=live_payment["payment_id"],
                merchant_id=merchant_id
            ).order_by(PaymentEventModel.created_at.asc()).all()

            # If no explicit events found in DB, return standard default timeline elements derived from live_payment
            if not records:
                events = [
                    {
                        "event_type": "ORDER_CREATED",
                        "description": f"Order {live_payment.get('razorpay_order_id', '')} created for ₹{live_payment.get('amount_inr', 0)}",
                        "created_at": live_payment.get("created_at")
                    },
                    {
                        "event_type": "PAYMENT_ATTEMPTED",
                        "description": f"Payment attempt recorded via {live_payment.get('payment_method', 'Card')}",
                        "created_at": live_payment.get("created_at")
                    }
                ]
                if live_payment.get("status") in ["captured", "verified"]:
                    events.append({
                        "event_type": "PAYMENT_SUCCESS",
                        "description": "Payment captured and verified",
                        "created_at": live_payment.get("updated_at")
                    })
                elif live_payment.get("status") == "failed":
                    events.append({
                        "event_type": "PAYMENT_FAILED",
                        "description": f"Payment failed: {live_payment.get('error_description') or 'Authorization failure'}",
                        "created_at": live_payment.get("updated_at")
                    })
                return events

            return [
                {
                    "event_type": r.event_type,
                    "description": r.event_description,
                    "created_at": r.created_at.isoformat() if isinstance(r.created_at, datetime) else str(r.created_at)
                }
                for r in records
            ]
        finally:
            db.close()

def get_recovery_action_service() -> RecoveryActionService:
    return RecoveryActionService()
