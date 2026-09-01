import sys
import os
import time

# Ensure backend directory is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import init_db, SessionLocal, InfrastructureIncidentModel, PaymentEventModel, LivePaymentModel
from services.root_cause_service import get_root_cause_service
from services.recommendation_service import get_recommendation_service
from services.live_payment_service import get_live_payment_service

def test_phase10_intelligence_consistency():
    print("=" * 70)
    print("RECOVERAI PHASE 10: REAL FAILURE INTELLIGENCE CONSISTENCY QA SUITE")
    print("=" * 70)

    client = TestClient(app)
    init_db()

    ts = int(time.time() * 1000)
    test_order_id = f"order_twpt10_{ts}"
    test_payment_id = f"pay_live_twpt10_{ts}"

    # Step 1: Pre-register live order (INR 1,000)
    print("\n[Test 1/6] Pre-registering INR 1,000 live order...")
    lps = get_live_payment_service()
    lps.create_live_order(
        razorpay_order_id=test_order_id,
        merchant_id="m_1004",
        amount_inr=1000.0,
        currency="INR"
    )
    print(f"[OK] Live Order Created: OrderID={test_order_id}, Amount=INR 1000.0")

    # Step 2: Simulate actual Razorpay failure webhook
    print("\n[Test 2/6] Sending payment.failed webhook (International Card Not Supported, INR 1,000)...")
    wh_payload = {
        "event": "payment.failed",
        "event_id": f"evt_p10_{ts}",
        "payload": {
            "payment": {
                "entity": {
                    "id": test_payment_id,
                    "order_id": test_order_id,
                    "amount": 100000, # 100,000 paise = ₹1,000
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "bank": "Razorpay Gateway",
                    "error_code": "international_transaction_not_allowed",
                    "error_description": "International cards are not supported",
                    "error_reason": "card_not_supported",
                    "notes": {
                        "merchant_id": "m_1004",
                        "source": "RecoverAI"
                    }
                }
            }
        }
    }

    res_wh = client.post("/api/webhooks/razorpay", json=wh_payload)
    assert res_wh.status_code == 200, f"Webhook failed: {res_wh.text}"
    print("[OK] Webhook processed cleanly by backend")

    # Step 3: Verify Root Cause Analysis
    print("\n[Test 3/6] Verifying Root Cause Diagnosis classification...")
    rc_service = get_root_cause_service()
    rc_result = rc_service.analyze_root_cause(test_payment_id)
    assert rc_result is not None, "Root cause result is None!"

    primary = rc_result.get("primary_root_cause", {})
    cause_title = primary.get("title")
    category = primary.get("category")
    reason_text = primary.get("reason")

    assert cause_title == "Payment Method / Card Restriction", f"Expected 'Payment Method / Card Restriction', got '{cause_title}'"
    assert category == "Payment Method Restriction", f"Expected 'Payment Method Restriction', got '{category}'"
    print(f"[OK] Root Cause Diagnosis Verified: Category='{category}', Cause='{cause_title}'")
    print(f"     Explanation: {reason_text}")

    # Step 4: Verify Recommendation Strategy
    print("\n[Test 4/6] Verifying Recovery Recommendation Strategy...")
    rec_service = get_recommendation_service()
    rec_result = rec_service.recommend_recovery_strategy(test_payment_id)
    assert rec_result is not None, "Recommendation result is None!"

    rec_strat = rec_result.get("recommended_strategy", {}).get("strategy")
    assert rec_strat == "Alternate payment method", f"Expected 'Alternate payment method', got '{rec_strat}'"
    print(f"[OK] Recovery Recommendation Verified: Top Strategy='{rec_strat}'")

    # Step 5: Verify Infrastructure Incident Amount (INR 1,000) & Payment Association
    print("\n[Test 5/6] Verifying Infrastructure Incident Amount (INR 1,000) & Payment Association...")
    db = SessionLocal()
    try:
        inc = db.query(InfrastructureIncidentModel).filter(
            (InfrastructureIncidentModel.payment_id == test_payment_id) |
            (InfrastructureIncidentModel.gateway == "Razorpay Gateway")
        ).order_by(InfrastructureIncidentModel.created_at.desc()).first()

        assert inc is not None, f"No incident found for payment or gateway"
        assert inc.amount_at_risk >= 1000.0, f"Expected amount_at_risk >= 1000.0, got {inc.amount_at_risk}"
        assert inc.source == "razorpay_test_webhook", f"Expected razorpay_test_webhook, got {inc.source}"
        print(f"[OK] Infrastructure Incident Verified: ID={inc.incident_id}, Gateway={inc.gateway}, Impact=INR {inc.amount_at_risk}")

        # Step 6: Verify Timeline Event Logs & Descriptions
        print("\n[Test 6/6] Verifying Timeline Audit Trail descriptions & amount propagation...")
        events = db.query(PaymentEventModel).filter(
            PaymentEventModel.payment_id == test_payment_id
        ).order_by(PaymentEventModel.created_at.asc()).all()

        evt_map = {e.event_type: e.event_description for e in events}
        assert "PAYMENT_FAILED" in evt_map, "Missing PAYMENT_FAILED event"
        assert "INFRASTRUCTURE_INCIDENT_DETECTED" in evt_map, "Missing INFRASTRUCTURE_INCIDENT_DETECTED event"

        assert "International cards are not supported" in evt_map["PAYMENT_FAILED"], f"Unexpected failure desc: {evt_map['PAYMENT_FAILED']}"
        assert "1,000.00" in evt_map["INFRASTRUCTURE_INCIDENT_DETECTED"], f"Unexpected incident desc: {evt_map['INFRASTRUCTURE_INCIDENT_DETECTED']}"

        print(f"[OK] Payment Timeline Verified: {len(events)} events logged chronologically")
        for e in events:
            safe_desc = e.event_description.encode('ascii', 'replace').decode('ascii')
            print(f"  - [{e.event_type}]: {safe_desc}")
    finally:
        db.close()

    print("\n" + "=" * 70)
    print("ALL 6 PHASE 10 FAILURE INTELLIGENCE CONSISTENCY TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_phase10_intelligence_consistency()
