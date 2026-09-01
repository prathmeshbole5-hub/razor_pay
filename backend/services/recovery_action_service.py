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

    def _determine_strategy_details(self, action_type: str, live_payment: Dict[str, Any]):
        act_lower = (action_type or "").lower()
        if "otp" in act_lower:
            strategy_name = "OTP Reminder"
            execution_status = "EXECUTED"
            result_msg = "OTP reminder recovery workflow dispatched to customer device in TEST_SIMULATION mode."
            next_step = "Await customer OTP re-entry."
            recovery_state = "AWAITING_RETRY"
        elif "link" in act_lower or "method" in act_lower or "alternate" in act_lower:
            strategy_name = "Alternate Payment Method"
            execution_status = "EXECUTED"
            result_msg = "Recovery action executed in TEST_SIMULATION mode. Customer instructed to retry using an alternate payment method."
            next_step = "Await customer payment retry via alternate channel."
            recovery_state = "AWAITING_RETRY"
        elif "later" in act_lower or "cool" in act_lower or "10" in act_lower:
            strategy_name = "Retry After 10 Minutes"
            execution_status = "SCHEDULED"
            result_msg = "Retry workflow scheduled according to recommended strategy in TEST_SIMULATION mode."
            next_step = "Auto-retry execution queued after cool-down."
            recovery_state = "RETRY_SCHEDULED"
        elif "manual" in act_lower:
            strategy_name = "Manual Support Outreach"
            execution_status = "EXECUTED"
            result_msg = "Manual support team follow-up task created in TEST_SIMULATION mode."
            next_step = "Merchant support team outreach pending."
            recovery_state = "AWAITING_RETRY"
        else:
            strategy_name = "Smart Gateway Retry"
            execution_status = "SCHEDULED"
            result_msg = "Smart gateway retry workflow scheduled in TEST_SIMULATION mode."
            next_step = "Auto-retry execution queued."
            recovery_state = "RETRY_SCHEDULED"

        return strategy_name, execution_status, result_msg, next_step, recovery_state

    def execute_recovery_action(
        self,
        payment_id: str,
        merchant_id: str,
        action_type: str
    ) -> Dict[str, Any]:
        """
        Executes a recovery action for a given payment after enforcing merchant domain isolation.
        Prevents duplicate execution of the same active action and produces enriched lifecycle audit records.
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
            strategy_name, execution_status, result_msg, next_step, recovery_state = self._determine_strategy_details(
                action_type, live_payment
            )

            # 2. Check for duplicate action execution
            existing_action = db.query(RecoveryActionModel).filter(
                RecoveryActionModel.payment_id == live_payment["payment_id"],
                RecoveryActionModel.merchant_id == merchant_id,
                RecoveryActionModel.action_type == action_type
            ).order_by(RecoveryActionModel.created_at.desc()).first()

            if existing_action:
                return {
                    "action_id": f"rec_{existing_action.id}",
                    "payment_id": live_payment["payment_id"],
                    "merchant_id": merchant_id,
                    "incident_id": getattr(existing_action, 'incident_id', None),
                    "strategy": getattr(existing_action, 'strategy_name', strategy_name) or strategy_name,
                    "execution_status": existing_action.status.upper() if existing_action.status else "EXECUTED",
                    "execution_mode": getattr(existing_action, 'execution_mode', 'TEST_SIMULATION') or 'TEST_SIMULATION',
                    "result": f"Recovery action already executed for payment. ({result_msg})",
                    "next_step": getattr(existing_action, 'next_step', next_step) or next_step,
                    "executed_at": existing_action.created_at.isoformat() if isinstance(existing_action.created_at, datetime) else str(existing_action.created_at),
                    "payment_status": str(live_payment.get("status", "failed")),
                    "recovery_status": getattr(existing_action, 'recovery_state', recovery_state) or recovery_state,
                    "already_executed": True,
                    "message": f"Recovery action '{action_type}' was already executed for payment '{payment_id}'."
                }

            # 3. Check for linked Infrastructure Incident
            incident_id = None
            try:
                from database import InfrastructureIncidentModel
                inc = db.query(InfrastructureIncidentModel).filter(
                    (InfrastructureIncidentModel.payment_id == live_payment["payment_id"]) |
                    (InfrastructureIncidentModel.gateway == live_payment.get("bank"))
                ).order_by(InfrastructureIncidentModel.created_at.desc()).first()
                if inc:
                    incident_id = inc.incident_id
            except Exception:
                pass

            now = datetime.utcnow()

            action_rec = RecoveryActionModel(
                payment_id=live_payment["payment_id"],
                merchant_id=merchant_id,
                action_type=action_type,
                incident_id=incident_id,
                execution_mode="TEST_SIMULATION",
                recovery_state=recovery_state,
                strategy_name=strategy_name,
                next_step=next_step,
                status="executed",
                execution_result=json.dumps({
                    "strategy": strategy_name,
                    "mode": "TEST_SIMULATION",
                    "result": result_msg,
                    "next_step": next_step,
                    "triggered_by": "merchant_portal"
                }),
                created_at=now,
                completed_at=now
            )
            db.add(action_rec)

            event_msg = f"Recovery Action Executed (TEST SIMULATION MODE): {strategy_name}. {result_msg}"

            # 4. Create payment event in timeline
            evt = PaymentEventModel(
                payment_id=live_payment["payment_id"],
                merchant_id=merchant_id,
                event_type="RECOVERY_ACTION_EXECUTED",
                event_description=event_msg,
                metadata_json=json.dumps({
                    "action": action_type,
                    "strategy": strategy_name,
                    "mode": "TEST_SIMULATION",
                    "status": "executed",
                    "result": result_msg,
                    "next_step": next_step
                }),
                created_at=now
            )
            db.add(evt)

            db.commit()
            db.refresh(action_rec)

            return {
                "action_id": f"rec_{action_rec.id}",
                "payment_id": live_payment["payment_id"],
                "merchant_id": merchant_id,
                "incident_id": incident_id,
                "strategy": strategy_name,
                "action": action_type,
                "action_type": action_type,
                "status": "executed",
                "execution_status": "EXECUTED",
                "execution_mode": "TEST_SIMULATION",
                "result": result_msg,
                "next_step": next_step,
                "executed_at": action_rec.created_at.isoformat(),
                "payment_status": str(live_payment.get("status", "failed")),
                "recovery_status": recovery_state,
                "already_executed": False,
                "message": event_msg
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

            result_list = []
            for r in records:
                parsed_res = None
                if r.execution_result:
                    try:
                        parsed_res = json.loads(r.execution_result)
                    except Exception:
                        parsed_res = {"detail": r.execution_result}

                strategy_name = getattr(r, 'strategy_name', None) or r.action_type.replace('_', ' ').title()
                exec_mode = getattr(r, 'execution_mode', None) or "TEST_SIMULATION"
                rec_state = getattr(r, 'recovery_state', None) or "AWAITING_RETRY"
                nxt_step = getattr(r, 'next_step', None) or "Await customer payment retry."

                result_list.append({
                    "action_id": f"rec_{r.id}",
                    "payment_id": r.payment_id,
                    "merchant_id": r.merchant_id,
                    "incident_id": getattr(r, 'incident_id', None),
                    "action_type": r.action_type,
                    "strategy": strategy_name,
                    "execution_status": r.status.upper() if r.status else "EXECUTED",
                    "execution_mode": exec_mode,
                    "recovery_state": rec_state,
                    "result": parsed_res.get("result") if isinstance(parsed_res, dict) else parsed_res,
                    "next_step": nxt_step,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if isinstance(r.created_at, datetime) else str(r.created_at)
                })
            return result_list
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
