import os
import json
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from services.simulation_service import get_simulation_service
from database import (
    SessionLocal,
    LivePaymentModel,
    AIIntelligenceResultModel,
    RecoveryActionModel,
    PaymentEventModel,
    WebhookEventModel
)

DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() in ("true", "1", "yes")

router = APIRouter(prefix="/api/demo", tags=["Demo Simulation & Reset Layer"])
sim_service = get_simulation_service()

@router.get("/events")
def get_simulated_events():
    """
    Returns recent in-memory simulated payment failure and recovery events.
    """
    return {
        "events": sim_service.get_events(),
        "total_events": len(sim_service.get_events())
    }

@router.post("/simulate")
def trigger_simulated_event(event_type: str = Query("failure", description="Event type: failure | gateway_spike | recovery")):
    """
    Triggers a new in-memory simulated event without modifying original CSV datasets.
    """
    event = sim_service.simulate_event(event_type)
    return {
        "status": "Event Simulated Successfully",
        "event": event
    }

@router.post("/reset")
def reset_simulated_events():
    """
    Resets the in-memory simulation state to clean baseline.
    """
    sim_service.reset_simulation()
    return {
        "status": "Simulation State Reset Successfully"
    }

@router.post("/reset-all")
def reset_all_demo_data():
    """
    Controlled Demo Reset mechanism.
    Protected by DEMO_MODE environment variable.
    Clears generated demo/live payment records, intelligence results, recovery actions, payment events, and webhook events from SQLite DB.
    PRESERVES original CSV datasets, ML model files, and application source code.
    """
    if not DEMO_MODE:
        raise HTTPException(status_code=403, detail="Demo reset is disabled when DEMO_MODE=false.")

    db = SessionLocal()
    try:
        db.query(RecoveryActionModel).delete()
        db.query(AIIntelligenceResultModel).delete()
        db.query(PaymentEventModel).delete()
        db.query(WebhookEventModel).delete()
        db.query(LivePaymentModel).delete()
        db.commit()

        # Also reset in-memory simulator
        sim_service.reset_simulation()

        return {
            "status": "ok",
            "message": "All generated demo/live payment database records cleared successfully.",
            "demo_mode": DEMO_MODE
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset demo database: {str(e)}")
    finally:
        db.close()

@router.post("/seed")
def seed_demo_scenario():
    """
    Creates a deterministic, repeatable hackathon demo payment scenario.
    Protected by DEMO_MODE environment setting.
    Resets generated live records and inserts a high-value failed payment with ML intelligence and timeline.
    """
    if not DEMO_MODE:
        raise HTTPException(status_code=403, detail="Demo seed is disabled when DEMO_MODE=false.")

    # First reset existing live demo data
    reset_all_demo_data()

    db = SessionLocal()
    try:
        now = datetime.utcnow()
        pm_id = "pay_demo_seed_8c"
        ord_id = "order_demo_seed_8c"
        merchant_id = "m_1004"
        amt = 12499.0

        # 1. Create Live Payment record
        pm_rec = LivePaymentModel(
            payment_id=pm_id,
            order_id=ord_id,
            merchant_id=merchant_id,
            amount=amt,
            currency="INR",
            status="failed",
            payment_method="Card",
            bank="HDFC Bank",
            error_code="BAD_REQUEST_ABANDONED",
            error_description="3DS authentication timed out at issuer bank gateway",
            razorpay_payment_id="pay_demo_seed_8c",
            created_at=now,
            updated_at=now
        )
        db.add(pm_rec)

        # 2. Attach ML Intelligence payload
        root_cause_payload = {
            "payment_id": pm_id,
            "primary_root_cause": {
                "title": "Bank 3DS Authentication Timeout",
                "reason": "Customer 3DS verification timed out at HDFC issuer gateway due to peak session congestion.",
                "confidence": 0.94
            },
            "contributing_factors": [
                {"factor": "Network Latency", "detail": "High latency (320ms) logged on HDFC acquirer route during checkout window."},
                {"factor": "Customer Abandonment", "detail": "No OTP entry received within 120-second timeout window."}
            ]
        }

        recommendation_payload = {
            "payment_id": pm_id,
            "recommended_strategy": {
                "strategy": "Smart Cool-down Retry",
                "reason": "Bank congestion expected to clear within 12 minutes. Automated retry yields 84% conversion."
            },
            "alternative_strategies": [
                {"strategy": "OTP Reminder", "reason": "Send instant SMS/WhatsApp reminder to customer device."},
                {"strategy": "Payment Link", "reason": "Generate instant recovery payment link for cart drop."}
            ]
        }

        intel_rec = AIIntelligenceResultModel(
            payment_id=pm_id,
            recovery_probability=0.78,
            prediction_band="High Recovery Probability",
            confidence_score=0.92,
            prediction_mode="live_feature_adapter",
            feature_completeness=1.0,
            root_cause=json.dumps(root_cause_payload),
            root_cause_confidence=0.94,
            recommendation=json.dumps(recommendation_payload),
            recommendation_score=0.90,
            expected_recovery_rate=0.78,
            created_at=now
        )
        db.add(intel_rec)

        # 3. Create Timeline Events
        events = [
            PaymentEventModel(
                payment_id=pm_id, merchant_id=merchant_id, event_type="ORDER_CREATED",
                event_description=f"Order {ord_id} created for ₹{amt:,.2f} (Receipt: hackathon_demo_seed)",
                created_at=now
            ),
            PaymentEventModel(
                payment_id=pm_id, merchant_id=merchant_id, event_type="PAYMENT_ATTEMPTED",
                event_description="Card payment attempted via HDFC Bank 3DS gateway",
                created_at=now
            ),
            PaymentEventModel(
                payment_id=pm_id, merchant_id=merchant_id, event_type="PAYMENT_FAILED",
                event_description="Payment failed: 3DS authentication timed out at issuer bank gateway",
                created_at=now
            ),
            PaymentEventModel(
                payment_id=pm_id, merchant_id=merchant_id, event_type="ML_ANALYSIS_COMPLETED",
                event_description="ML recovery prediction calculated: 78.0% (High Recovery Probability)",
                created_at=now
            ),
            PaymentEventModel(
                payment_id=pm_id, merchant_id=merchant_id, event_type="ROOT_CAUSE_IDENTIFIED",
                event_description="Root cause identified: Bank 3DS Authentication Timeout (Confidence: 94%)",
                created_at=now
            ),
            PaymentEventModel(
                payment_id=pm_id, merchant_id=merchant_id, event_type="RECOMMENDATION_GENERATED",
                event_description="AI strategy recommended: Smart Cool-down Retry (Estimated Recovery Rate: 78%)",
                created_at=now
            )
        ]
        db.add_all(events)
        db.commit()

        return {
            "status": "ok",
            "message": "Deterministic hackathon demo scenario seeded successfully.",
            "seeded_payment_id": pm_id,
            "merchant_id": merchant_id,
            "amount_inr": amt,
            "recovery_probability": 78.0
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to seed demo scenario: {str(e)}")
    finally:
        db.close()
