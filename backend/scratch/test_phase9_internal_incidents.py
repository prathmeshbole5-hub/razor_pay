import sys
import os
import json

# Ensure backend path is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import init_db, SessionLocal, InfrastructureIncidentModel, PaymentEventModel, LivePaymentModel

def test_internal_incident_pipeline():
    print("=" * 65)
    print("RECOVERAI PHASE 9: REAL INCIDENT & RAZORPAY INTERNAL PORTAL QA SUITE")
    print("=" * 65)

    client = TestClient(app)
    init_db()

    # Step 1: Health & Incidents endpoint check
    print("[Test 1/6] GET /api/internal/incidents endpoint readiness...")
    res = client.get("/api/internal/incidents")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    incidents_list = res.json()
    assert isinstance(incidents_list, list), "Expected list response"
    print(f"[OK] GET /api/internal/incidents OK ({len(incidents_list)} incidents returned)")

    # Step 2: Simulate real Razorpay payment.failed webhook
    import time
    ts = int(time.time() * 1000)
    print("\n[Test 2/6] Triggering real payment.failed webhook...")
    test_payment_id = f"pay_wh_qa9_{ts}"
    test_order_id = f"order_wh_qa9_{ts}"

    # Pre-register live order (simulating create-order step)
    from services.live_payment_service import get_live_payment_service
    lps = get_live_payment_service()
    lps.create_live_order(
        razorpay_order_id=test_order_id,
        merchant_id="m_1004",
        amount_inr=750.0,
        currency="INR"
    )

    wh_payload = {
        "event": "payment.failed",
        "event_id": f"evt_qa9_{test_payment_id}",
        "payload": {
            "payment": {
                "entity": {
                    "id": test_payment_id,
                    "order_id": test_order_id,
                    "amount": 75000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "bank": "SBI",
                    "error_code": "BAD_REQUEST_TIMEOUT",
                    "error_description": "UPI PSP Gateway Timeout",
                    "error_reason": "payment_timed_out",
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
    wh_json = res_wh.json()
    assert wh_json.get("status") in ["ok", "ignored_duplicate"]
    print("[OK] Real payment.failed webhook processed successfully")

    # Step 3: Verify Infrastructure Incident creation in SQLite DB
    print("\n[Test 3/6] Verifying Infrastructure Incident creation in SQLite DB...")
    db = SessionLocal()
    try:
        recovered_rec = db.query(LivePaymentModel).filter(
            LivePaymentModel.order_id == test_order_id
        ).first()
        assert recovered_rec is not None, "Live payment record was not updated!"

        inc = db.query(InfrastructureIncidentModel).filter(
            (InfrastructureIncidentModel.payment_id == test_payment_id) |
            (InfrastructureIncidentModel.payment_id == recovered_rec.payment_id) |
            (InfrastructureIncidentModel.gateway == "SBI")
        ).order_by(InfrastructureIncidentModel.created_at.desc()).first()

        assert inc is not None, "Infrastructure incident was not created!"
        assert inc.gateway == "SBI", f"Expected SBI, got {inc.gateway}"
        assert inc.amount_at_risk > 0, f"Expected > 0, got {inc.amount_at_risk}"
        assert inc.source == "razorpay_test_webhook", f"Expected razorpay_test_webhook, got {inc.source}"
        print(f"[OK] SQLite Incident Verified: ID={inc.incident_id}, Title='{inc.title}', Risk=INR {inc.amount_at_risk}, Source={inc.source}")

        # Check Timeline Event INFRASTRUCTURE_INCIDENT_DETECTED
        recovered_rec = db.query(LivePaymentModel).filter(
            LivePaymentModel.order_id == test_order_id
        ).first()

        events = db.query(PaymentEventModel).filter(
            PaymentEventModel.payment_id == recovered_rec.payment_id
        ).all()
        event_types = [e.event_type for e in events]
        assert "INFRASTRUCTURE_INCIDENT_DETECTED" in event_types, f"Missing incident event in timeline! Got: {event_types}"
        print(f"[OK] Timeline Event Verified: INFRASTRUCTURE_INCIDENT_DETECTED present in {recovered_rec.payment_id} timeline ({len(events)} total events)")
        inc_id_for_mitigation = inc.incident_id
    finally:
        db.close()

    # Step 4: Verify Razorpay Internal API retrieves real incident
    print("\n[Test 4/6] Verifying GET /api/internal/incidents contains real webhook telemetry...")
    res_inc = client.get("/api/internal/incidents")
    assert res_inc.status_code == 200
    all_incidents = res_inc.json()
    matching = [i for i in all_incidents if i.get("gateway") == "SBI" and i.get("source") == "razorpay_test_webhook"]
    assert len(matching) > 0, "Real test incident not found in GET /api/internal/incidents response!"
    print(f"[OK] Razorpay Internal API returned real test incident: '{matching[0]['title']}'")

    # Step 5: Execute simulated mitigation
    print("\n[Test 5/6] Executing simulated mitigation POST /api/internal/incidents/{incident_id}/mitigate...")
    res_mit = client.post(f"/api/internal/incidents/{inc_id_for_mitigation}/mitigate")
    assert res_mit.status_code == 200, f"Mitigation failed: {res_mit.text}"
    mit_json = res_mit.json()
    assert mit_json.get("status") == "mitigated"
    assert mit_json.get("mode") == "test_simulation"
    print(f"[OK] Mitigation Response Verified: {mit_json}")

    # Step 6: Verify status update to MITIGATED & timeline event MITIGATION_EXECUTED
    print("\n[Test 6/6] Verifying SQLite persistence of MITIGATED status and timeline audit trail...")
    db = SessionLocal()
    try:
        updated_inc = db.query(InfrastructureIncidentModel).filter(
            InfrastructureIncidentModel.incident_id == inc_id_for_mitigation
        ).first()
        assert updated_inc.status == "MITIGATED", f"Expected MITIGATED, got {updated_inc.status}"
        assert updated_inc.mitigated_at is not None, "mitigated_at timestamp is None!"

        events_after = db.query(PaymentEventModel).filter(
            PaymentEventModel.payment_id == recovered_rec.payment_id
        ).all()
        types_after = [e.event_type for e in events_after]
        assert "MITIGATION_EXECUTED" in types_after, f"Missing MITIGATION_EXECUTED in timeline! Got: {types_after}"
        print(f"[OK] SQLite Mitigation Verified: Status={updated_inc.status}, MitigatedAt={updated_inc.mitigated_at}")
        print(f"[OK] Payment Timeline Audit Trail Verified: {types_after}")
    finally:
        db.close()

    print("=" * 65)
    print("ALL 6 PHASE 9 INFRASTRUCTURE INCIDENT TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    test_internal_incident_pipeline()
