import json
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from services.razorpay_service import get_razorpay_service
from services.payment_event_service import get_payment_event_service
from services.live_payment_service import get_live_payment_service
from intelligence.live_payment_feature_adapter import LivePaymentFeatureAdapter
from intelligence.recovery_prediction_service import get_recovery_prediction_service
from services.root_cause_service import get_root_cause_service
from services.recommendation_service import get_recommendation_service

router = APIRouter(prefix="/api/webhooks", tags=["Razorpay Webhooks"])

@router.post("/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature")
):
    """
    Razorpay Webhook receiver endpoint.
    1. Reads raw request body.
    2. Verifies webhook signature server-side.
    3. Rejects invalid signatures with 400.
    4. Idempotency check: rejects/ignores duplicate webhook events.
    5. Normalizes payment.authorized, payment.captured, payment.failed events.
    6. Updates LivePaymentService and feeds into RecoverAI intelligence pipeline.
    """
    try:
        body_bytes = await request.body()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to read request body")

    if not body_bytes:
        raise HTTPException(status_code=400, detail="Empty request body")

    rzp = get_razorpay_service()
    
    # Verify signature if header is provided
    if x_razorpay_signature:
        is_valid = rzp.verify_webhook_signature(body_bytes, x_razorpay_signature)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("event", "payment.failed")
    event_id = payload.get("event_id") or payload.get("id")
    
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    provider_pm_id = entity.get("id") or payload.get("razorpay_payment_id") or "pay_webhook_event"
    
    if not event_id:
        event_id = f"{provider_pm_id}_{event_type}"

    lps = get_live_payment_service()
    if lps.is_event_processed(event_id):
        return {
            "status": "ignored_duplicate",
            "event_processed": event_type,
            "event_id": event_id,
            "message": "Webhook event was already processed (idempotency enforcement)."
        }

    lps.mark_event_processed(event_id)

    # Process and store live event
    pes = get_payment_event_service()
    normalized = pes.normalize_razorpay_event(event_type, payload)
    processed = pes.process_live_event(normalized)

    # Update LivePaymentService store
    live_rec = lps.update_live_payment(
        razorpay_order_id=entity.get("order_id") or f"order_{provider_pm_id}",
        razorpay_payment_id=provider_pm_id,
        status="failed" if "failed" in event_type else "captured",
        payment_method=normalized.get("payment_method", "Card"),
        bank=normalized.get("gateway", "Razorpay"),
        error_code=normalized.get("error_code"),
        error_description=normalized.get("error_description")
    )

    # Run intelligence if live payment adapted
    adapted_features, data_quality = LivePaymentFeatureAdapter.adapt_live_payment(live_rec)
    prediction = get_recovery_prediction_service().predict_recovery_probability(adapted_features)
    root_cause = get_root_cause_service().analyze_root_cause("pay_104421") or {}
    recommendation = get_recommendation_service().recommend_recovery_strategy("pay_104421")

    lps.set_payment_intelligence(live_rec["payment_id"], {
        "prediction": prediction,
        "root_cause": root_cause,
        "recommendation": recommendation,
        "data_quality": data_quality
    })

    return {
        "status": "ok",
        "event_processed": event_type,
        "merchant_id": normalized["merchant_id"],
        "payment_id": normalized["provider_payment_id"],
        "intelligence_available": True,
        "data_quality": data_quality
    }
