import sys
import os
import json
from datetime import datetime
from fastapi.testclient import TestClient

# Ensure backend directory is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from database import init_db, SessionLocal, LivePaymentModel, RecoveryActionModel, PaymentEventModel, InfrastructureIncidentModel, AIIntelligenceResultModel
from services.live_payment_service import LivePaymentService
from services.recovery_action_service import RecoveryActionService
from services.infrastructure_incident_service import InfrastructureIncidentService
from services.merchant_service import MerchantService

client = TestClient(app)

def test_api_error_states_suite():
    print("=" * 75)
    print("RECOVERAI QA SUITE: GLOBAL UX RELIABILITY & API ERROR CONTRACT")
    print("=" * 75)

    init_db()
    lps = LivePaymentService()
    ras = RecoveryActionService()
    iis = InfrastructureIncidentService()
    ms = MerchantService()

    def clear_db():
        db = SessionLocal()
        try:
            db.query(PaymentEventModel).delete()
            db.query(RecoveryActionModel).delete()
            db.query(AIIntelligenceResultModel).delete()
            db.query(InfrastructureIncidentModel).delete()
            db.query(LivePaymentModel).delete()
            db.commit()
        finally:
            db.close()

    clear_db()

    # ----------------------------------------------------
    # TEST 1: Missing Merchant ID returns 404
    # ----------------------------------------------------
    print("\n[Test 1] Missing/invalid merchant ID returns HTTP 404...")
    r1 = client.get("/api/merchant/dashboard?merchant_id=m_invalid_9999")
    assert r1.status_code == 404, f"Expected 404 for invalid merchant, got {r1.status_code}"
    assert "not found" in r1.json()["detail"].lower()
    print("[OK] Test 1 Passed: Invalid merchant ID returned HTTP 404 with structured error.")

    # ----------------------------------------------------
    # TEST 2: Missing Payment ID returns 404
    # ----------------------------------------------------
    print("\n[Test 2] Missing/invalid live payment ID returns HTTP 404...")
    r2 = client.get("/api/merchant/live-payments/pay_non_existent_123/intelligence?merchant_id=m_1004")
    assert r2.status_code == 404, f"Expected 404 for missing payment, got {r2.status_code}"
    print("[OK] Test 2 Passed: Missing payment ID returned HTTP 404.")

    # ----------------------------------------------------
    # TEST 3: Missing Incident ID returns 404
    # ----------------------------------------------------
    print("\n[Test 3] Missing/invalid infrastructure incident ID returns HTTP 404...")
    r3 = client.get("/api/internal/incidents/inc_non_existent_999")
    assert r3.status_code == 404, f"Expected 404 for missing incident, got {r3.status_code}"

    r3_p = client.get("/api/internal/incidents/inc_non_existent_999/payments")
    assert r3_p.status_code == 404, f"Expected 404 for missing incident affected payments, got {r3_p.status_code}"

    r3_m = client.post("/api/internal/incidents/inc_non_existent_999/mitigate")
    assert r3_m.status_code == 404, f"Expected 404 for mitigating missing incident, got {r3_m.status_code}"
    print("[OK] Test 3 Passed: Missing incident endpoints returned HTTP 404.")

    # ----------------------------------------------------
    # TEST 4: Invalid Order Amount returns 400 / 422
    # ----------------------------------------------------
    print("\n[Test 4] Invalid order creation parameters return HTTP 400 / 422...")
    r4 = client.post("/api/payments/create-order", json={"amount": -500.0, "merchant_id": "m_1004"})
    assert r4.status_code in (400, 422), f"Expected 400 or 422 for negative amount, got {r4.status_code}"
    print(f"[OK] Test 4 Passed: Negative order amount returned validation error (HTTP {r4.status_code}).")

    # ----------------------------------------------------
    # TEST 5: Invalid Payment Signature returns 400
    # ----------------------------------------------------
    print("\n[Test 5] Invalid payment signature verification returns HTTP 400...")
    r5 = client.post("/api/payments/verify", json={
        "razorpay_payment_id": "pay_fake_123",
        "razorpay_order_id": "order_fake_123",
        "razorpay_signature": "invalid_sig_abc",
        "merchant_id": "m_1004"
    })
    assert r5.status_code == 400, f"Expected 400 for invalid signature, got {r5.status_code}"
    print("[OK] Test 5 Passed: Invalid payment signature returned HTTP 400.")

    # ----------------------------------------------------
    # TEST 6: Empty Transaction Data returns structured zero metrics
    # ----------------------------------------------------
    print("\n[Test 6] Empty transaction database returned structured metrics...")
    r6 = client.get("/api/merchant/dashboard?merchant_id=m_1004")
    assert r6.status_code == 200
    data6 = r6.json()
    assert "revenue_at_risk" in data6 and "revenue_recovered" in data6
    print("[OK] Test 6 Passed: Empty database returned valid zero metrics structure.")

    # ----------------------------------------------------
    # TEST 7: Duplicate Action Execution Idempotency
    # ----------------------------------------------------
    print("\n[Test 7] Duplicate action execution returns already_executed=true...")
    merchant_id = "m_1004"
    pay_id = "pay_live_err_01"
    
    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id=pay_id,
            order_id="order_err_01",
            merchant_id=merchant_id,
            amount=1000.0,
            status="failed",
            error_code="BAD_REQUEST"
        ))
        db.commit()
    finally:
        db.close()

    res_act1 = ras.execute_recovery_action(pay_id, merchant_id, "payment_link")
    assert res_act1["already_executed"] is False

    res_act2 = ras.execute_recovery_action(pay_id, merchant_id, "payment_link")
    assert res_act2["already_executed"] is True
    print("[OK] Test 7 Passed: Duplicate action execution returned already_executed=true.")

    # ----------------------------------------------------
    # TEST 8: Already Mitigated Incident Handling
    # ----------------------------------------------------
    print("\n[Test 8] Already mitigated incident handling...")
    inc_id = "inc_err_01"
    db = SessionLocal()
    try:
        db.add(InfrastructureIncidentModel(
            incident_id=inc_id,
            payment_id=pay_id,
            merchant_id=merchant_id,
            gateway="SBI Card Gateway",
            payment_method="Card",
            title="Test Incident",
            severity="HIGH",
            status="ACTIVE",
            source="razorpay_test_webhook",
            amount_at_risk=1000.0
        ))
        db.commit()
    finally:
        db.close()

    mit1 = iis.mitigate_incident(inc_id)
    assert mit1["status"] == "mitigated"

    mit2 = iis.mitigate_incident(inc_id)
    assert mit2["status"] == "mitigated"
    print("[OK] Test 8 Passed: Mitigating incident twice returned mitigated state idempotently.")

    clear_db()
    print("=" * 75)
    print("ALL GLOBAL UX RELIABILITY & API ERROR STATE QA TESTS PASSED!")
    print("=" * 75)

if __name__ == "__main__":
    test_api_error_states_suite()
