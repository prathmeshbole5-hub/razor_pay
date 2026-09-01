import json
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from database import (
    SessionLocal,
    LivePaymentModel,
    AIIntelligenceResultModel,
    PaymentEventModel,
    WebhookEventModel
)

class LivePaymentService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LivePaymentService, cls).__new__(cls)
            return cls._instance

    def _model_to_dict(self, model: LivePaymentModel, db_session=None) -> Dict[str, Any]:
        if not model:
            return None
        
        intel_dict = None
        if db_session:
            intel_row = db_session.query(AIIntelligenceResultModel).filter_by(payment_id=model.payment_id).order_by(AIIntelligenceResultModel.created_at.desc()).first()
            if intel_row:
                try:
                    rc = json.loads(intel_row.root_cause) if intel_row.root_cause else None
                except Exception:
                    rc = intel_row.root_cause

                try:
                    rec = json.loads(intel_row.recommendation) if intel_row.recommendation else None
                except Exception:
                    rec = intel_row.recommendation

                intel_dict = {
                    "prediction": {
                        "recovery_probability": intel_row.recovery_probability,
                        "probability_band": intel_row.prediction_band,
                        "prediction_class": intel_row.prediction_band,
                        "confidence_score": intel_row.confidence_score or 0.92,
                        "prediction_mode": intel_row.prediction_mode or "live_feature_adapter"
                    },
                    "root_cause": rc,
                    "recommendation": rec,
                    "data_quality": {
                        "feature_completeness": intel_row.feature_completeness or 1.0,
                        "is_complete": (intel_row.feature_completeness or 1.0) >= 0.8
                    }
                }

        return {
            "payment_id": model.payment_id,
            "merchant_id": model.merchant_id,
            "razorpay_order_id": model.order_id,
            "razorpay_payment_id": model.razorpay_payment_id,
            "amount": round(float(model.amount), 2),
            "amount_inr": round(float(model.amount), 2),
            "currency": model.currency or "INR",
            "status": model.status,
            "payment_method": model.payment_method or "Card",
            "bank": model.bank or "Razorpay Gateway",
            "error_code": model.error_code,
            "error_description": model.error_description,
            "source": "razorpay_test_mode",
            "created_at": model.created_at.isoformat() if isinstance(model.created_at, datetime) else str(model.created_at),
            "updated_at": model.updated_at.isoformat() if isinstance(model.updated_at, datetime) else str(model.updated_at),
            "intelligence": intel_dict
        }

    def _log_event(self, db_session, payment_id: str, merchant_id: str, event_type: str, description: str, metadata: Optional[Dict[str, Any]] = None):
        evt = PaymentEventModel(
            payment_id=payment_id,
            merchant_id=merchant_id,
            event_type=event_type,
            event_description=description,
            metadata_json=json.dumps(metadata) if metadata else None,
            created_at=datetime.utcnow()
        )
        db_session.add(evt)

    def create_live_order(
        self,
        razorpay_order_id: str,
        merchant_id: str,
        amount_inr: float,
        currency: str = "INR",
        receipt: str = "recoverai_demo_order"
    ) -> Dict[str, Any]:
        """
        Stores an initial live payment/order record in SQLite database.
        Logs ORDER_CREATED event.
        """
        with self._lock:
            db = SessionLocal()
            try:
                recoverai_payment_id = f"pay_live_{razorpay_order_id.replace('order_', '')}"
                
                # Check if order already exists
                existing = db.query(LivePaymentModel).filter_by(payment_id=recoverai_payment_id).first()
                if not existing:
                    existing = LivePaymentModel(
                        payment_id=recoverai_payment_id,
                        order_id=razorpay_order_id,
                        merchant_id=merchant_id,
                        amount=round(float(amount_inr), 2),
                        currency=currency.upper(),
                        status="created",
                        payment_method="Card",
                        bank="Razorpay Test Gateway",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(existing)

                    # Log ORDER_CREATED event
                    self._log_event(
                        db,
                        payment_id=recoverai_payment_id,
                        merchant_id=merchant_id,
                        event_type="ORDER_CREATED",
                        description=f"Order created for ₹{amount_inr:.2f} (Receipt: {receipt})",
                        metadata={"order_id": razorpay_order_id, "amount": amount_inr, "receipt": receipt}
                    )
                    db.commit()
                    db.refresh(existing)

                return self._model_to_dict(existing, db)
            finally:
                db.close()

    def update_live_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        status: str,
        payment_method: str = "Card",
        bank: Optional[str] = None,
        error_code: Optional[str] = None,
        error_description: Optional[str] = None,
        amount_inr: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Updates live payment status and fields after signature verification or webhook receipt in SQLite database.
        Logs payment events (PAYMENT_ATTEMPTED, PAYMENT_SUCCESS, PAYMENT_FAILED).
        """
        with self._lock:
            db = SessionLocal()
            try:
                record = db.query(LivePaymentModel).filter(
                    (LivePaymentModel.order_id == razorpay_order_id) |
                    (LivePaymentModel.payment_id == razorpay_payment_id) |
                    (LivePaymentModel.razorpay_payment_id == razorpay_payment_id)
                ).first()

                recoverai_payment_id = record.payment_id if record else (
                    razorpay_payment_id if razorpay_payment_id.startswith("pay_") else f"pay_{razorpay_payment_id}"
                )
                merchant_id = record.merchant_id if record else "m_1004"

                if not record:
                    record = LivePaymentModel(
                        payment_id=recoverai_payment_id,
                        order_id=razorpay_order_id,
                        merchant_id=merchant_id,
                        amount=float(amount_inr) if amount_inr else 500.0,
                        currency="INR",
                        status=status,
                        payment_method=payment_method or "Card",
                        bank=bank or "Razorpay Gateway",
                        error_code=error_code,
                        error_description=error_description,
                        razorpay_payment_id=razorpay_payment_id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(record)
                    self._log_event(
                        db,
                        payment_id=recoverai_payment_id,
                        merchant_id=merchant_id,
                        event_type="PAYMENT_ATTEMPTED",
                        description=f"Payment attempt recorded for order {razorpay_order_id}"
                    )
                else:
                    record.razorpay_payment_id = razorpay_payment_id
                    record.status = status
                    if amount_inr and amount_inr > 0:
                        record.amount = float(amount_inr)
                    if payment_method:
                        record.payment_method = payment_method
                    if bank:
                        record.bank = bank
                    if error_code:
                        record.error_code = error_code
                    if error_description:
                        record.error_description = error_description
                    record.updated_at = datetime.utcnow()

                # Log timeline events according to status
                if status in ["captured", "verified", "successful"]:
                    self._log_event(
                        db,
                        payment_id=recoverai_payment_id,
                        merchant_id=merchant_id,
                        event_type="PAYMENT_SUCCESS",
                        description=f"Payment verified successfully via {payment_method or 'Card'}"
                    )
                elif status in ["failed"]:
                    self._log_event(
                        db,
                        payment_id=recoverai_payment_id,
                        merchant_id=merchant_id,
                        event_type="PAYMENT_FAILED",
                        description=f"Payment failed via {payment_method or 'Card'}. Reason: {error_description or error_code or 'Authorization failure'}"
                    )
                else:
                    self._log_event(
                        db,
                        payment_id=recoverai_payment_id,
                        merchant_id=merchant_id,
                        event_type="PAYMENT_ATTEMPTED",
                        description=f"Payment status updated to {status}"
                    )

                db.commit()
                db.refresh(record)
                return self._model_to_dict(record, db)
            finally:
                db.close()

    def set_payment_intelligence(self, payment_id: str, intelligence_payload: Dict[str, Any]):
        """Attaches RecoverAI intelligence output to live payment record in SQLite database and logs timeline events."""
        with self._lock:
            db = SessionLocal()
            try:
                rec = db.query(LivePaymentModel).filter_by(payment_id=payment_id).first()
                if not rec:
                    return

                prediction = intelligence_payload.get("prediction") or {}
                root_cause = intelligence_payload.get("root_cause") or {}
                recommendation = intelligence_payload.get("recommendation") or {}
                data_quality = intelligence_payload.get("data_quality") or {}

                prob = prediction.get("recovery_probability", 0.65)
                band = prediction.get("probability_band") or prediction.get("prediction_class") or "Medium Recovery Probability"
                completeness = data_quality.get("feature_completeness", 1.0)

                intel = AIIntelligenceResultModel(
                    payment_id=payment_id,
                    recovery_probability=prob,
                    prediction_band=band,
                    confidence_score=prediction.get("confidence_score", 0.92),
                    prediction_mode="live_feature_adapter",
                    feature_completeness=completeness,
                    root_cause=json.dumps(root_cause),
                    root_cause_confidence=0.88,
                    recommendation=json.dumps(recommendation),
                    recommendation_score=0.90,
                    expected_recovery_rate=prob,
                    created_at=datetime.utcnow()
                )
                db.add(intel)

                # Log events in timeline
                self._log_event(
                    db,
                    payment_id=payment_id,
                    merchant_id=rec.merchant_id,
                    event_type="ML_ANALYSIS_COMPLETED",
                    description=f"ML recovery prediction calculated: {round(prob * 100, 1)}% ({band})"
                )
                self._log_event(
                    db,
                    payment_id=payment_id,
                    merchant_id=rec.merchant_id,
                    event_type="ROOT_CAUSE_IDENTIFIED",
                    description=f"Root cause analyzed: {root_cause.get('primary_root_cause', {}).get('title', '3DS Auth Timeout')}"
                )
                self._log_event(
                    db,
                    payment_id=payment_id,
                    merchant_id=rec.merchant_id,
                    event_type="RECOMMENDATION_GENERATED",
                    description=f"Recommendation generated: {recommendation.get('recommended_strategy', {}).get('strategy', 'Smart Gateway Retry')}"
                )

                db.commit()
            finally:
                db.close()

    def get_live_payment(self, payment_id: str, merchant_id: str) -> Optional[Dict[str, Any]]:
        """
        Enforces merchant domain isolation. Returns 404/None if payment belongs to another merchant.
        Queries SQLite database.
        """
        db = SessionLocal()
        try:
            record = db.query(LivePaymentModel).filter(
                (LivePaymentModel.payment_id == payment_id) |
                (LivePaymentModel.razorpay_payment_id == payment_id) |
                (LivePaymentModel.order_id == payment_id)
            ).first()

            if record and record.merchant_id == merchant_id:
                return self._model_to_dict(record, db)
            return None
        finally:
            db.close()

    def get_merchant_live_payments(self, merchant_id: str) -> List[Dict[str, Any]]:
        """Returns all live payment records for a given merchant from SQLite database, sorted newest first."""
        db = SessionLocal()
        try:
            records = db.query(LivePaymentModel).filter_by(merchant_id=merchant_id).order_by(LivePaymentModel.updated_at.desc()).all()
            return [self._model_to_dict(r, db) for r in records]
        finally:
            db.close()

    def is_event_processed(self, event_id: str) -> bool:
        """Idempotency check: Returns True if webhook/event ID was already processed in SQLite DB."""
        db = SessionLocal()
        try:
            row = db.query(WebhookEventModel).filter_by(event_id=event_id).first()
            return row is not None
        finally:
            db.close()

    def mark_event_processed(self, event_id: str, payment_id: Optional[str] = None, event_type: str = "webhook"):
        """Idempotency tracking: Marks webhook/event ID as processed in SQLite DB."""
        with self._lock:
            db = SessionLocal()
            try:
                row = db.query(WebhookEventModel).filter_by(event_id=event_id).first()
                if not row:
                    row = WebhookEventModel(
                        event_id=event_id,
                        payment_id=payment_id,
                        event_type=event_type,
                        processed=True,
                        created_at=datetime.utcnow()
                    )
                    db.add(row)

                    if payment_id:
                        payment = db.query(LivePaymentModel).filter_by(payment_id=payment_id).first()
                        merchant_id = payment.merchant_id if payment else "m_1004"
                        self._log_event(
                            db,
                            payment_id=payment_id,
                            merchant_id=merchant_id,
                            event_type="WEBHOOK_RECEIVED",
                            description=f"Received webhook event '{event_type}' (ID: {event_id})"
                        )
                        self._log_event(
                            db,
                            payment_id=payment_id,
                            merchant_id=merchant_id,
                            event_type="WEBHOOK_VERIFIED",
                            description=f"Webhook signature verified and processed idempotently"
                        )
                    db.commit()
            finally:
                db.close()


def get_live_payment_service() -> LivePaymentService:
    return LivePaymentService()
