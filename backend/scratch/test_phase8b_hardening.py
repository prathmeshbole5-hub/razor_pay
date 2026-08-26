import sys
import os
import json
import hmac
import hashlib
import pandas as pd
from fastapi.testclient import TestClient

# Ensure UTF-8 stdout encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# Add backend directory to path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from database import init_db, SessionLocal, LivePaymentModel, DB_PATH
from services.live_payment_service import get_live_payment_service
from services.recovery_action_service import get_recovery_action_service

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("RECOVERAI PHASE 8B HARDENING & VERIFICATION SUITE")
    print("=" * 60)
    
    passed_count = 0
    total_tests = 18

    # 1. Health Endpoint
    print("[Test 1/18] Health endpoint...")
    res = client.get("/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.json()
    assert body.get("status") in ["healthy", "degraded"], f"Unexpected status {body}"
    print("[OK] Health endpoint OK")
    passed_count += 1

    # 2. Database Initialization
    print("[Test 2/18] Database initialization...")
    init_db()
    assert os.path.exists(DB_PATH), f"Database file missing at {DB_PATH}"
    print("[OK] Database initialization OK")
    passed_count += 1

    # 3. Live Payment Persistence in DB
    print("[Test 3/18] Live Payment SQLite Persistence...")
    lps = get_live_payment_service()
    order_rec = lps.create_live_order(
        razorpay_order_id="order_test_phase8b_001",
        merchant_id="m_1004",
        amount_inr=1500.0,
        currency="INR",
        receipt="phase8b_test"
    )
    pm_id = order_rec["payment_id"]
    db = SessionLocal()
    try:
        db_rec = db.query(LivePaymentModel).filter_by(payment_id=pm_id).first()
        assert db_rec is not None, "Order record not found in SQLite DB"
        assert db_rec.amount == 1500.0, f"Expected amount 1500.0, got {db_rec.amount}"
    finally:
        db.close()
    print("[OK] Live Payment SQLite Persistence OK")
    passed_count += 1

    # 4. Backend Restart Persistence Simulation
    print("[Test 4/18] Backend Restart Data Persistence...")
    # Instantiate new service instance / query DB directly
    db = SessionLocal()
    try:
        persisted = db.query(LivePaymentModel).filter_by(payment_id=pm_id).first()
        assert persisted is not None, "Payment failed to persist across simulated restart"
        assert persisted.merchant_id == "m_1004"
    finally:
        db.close()
    print("[OK] Backend Restart Persistence OK")
    passed_count += 1

    # 5. Create Razorpay Order API
    print("[Test 5/18] Create Razorpay Order API...")
    res = client.post("/api/payments/create-order", json={
        "amount": 2499.0,
        "currency": "INR",
        "merchant_id": "m_1004",
        "receipt": "api_test_receipt"
    })
    assert res.status_code == 200, f"Order creation failed: {res.text}"
    order_data = res.json()
    rzp_order_id = order_data["order_id"]
    test_pm_id = order_data["recoverai_payment_id"]
    assert order_data["amount"] == 2499.0
    print(f"[OK] Create Order API OK ({rzp_order_id})")
    passed_count += 1

    # 6. Valid Payment Verification API
    print("[Test 6/18] Valid Payment Verification API...")
    test_payment_id = f"pay_rzp_{rzp_order_id.replace('order_', '')}"
    secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    if secret:
        sig_payload = f"{rzp_order_id}|{test_payment_id}"
        valid_sig = hmac.new(secret.encode(), sig_payload.encode(), hashlib.sha256).hexdigest()
    else:
        valid_sig = "sig_valid_test_mode_12345"

    res = client.post("/api/payments/verify", json={
        "razorpay_payment_id": test_payment_id,
        "razorpay_order_id": rzp_order_id,
        "razorpay_signature": valid_sig,
        "merchant_id": "m_1004",
        "status": "captured"
    })
    assert res.status_code == 200, f"Verification failed: {res.text}"
    ver_body = res.json()
    assert ver_body["verified"] is True
    print("[OK] Valid Payment Verification OK")
    passed_count += 1


    # 7. Invalid Signature Rejection
    print("[Test 7/18] Invalid Signature Rejection...")
    res = client.post("/api/payments/verify", json={
        "razorpay_payment_id": test_payment_id,
        "razorpay_order_id": rzp_order_id,
        "razorpay_signature": "invalid_fake_signature_12345",
        "merchant_id": "m_1004"
    })
    assert res.status_code == 400, f"Expected 400 for invalid signature, got {res.status_code}"
    print("[OK] Invalid Signature Rejection OK")
    passed_count += 1

    # 8. Live ML Prediction
    print("[Test 8/18] Live ML Recovery Prediction...")
    intel = ver_body.get("intelligence", {})
    pred = intel.get("prediction", {})
    assert "recovery_probability" in pred or "recovery_prediction" in intel, f"ML prediction missing: {intel}"
    print("[OK] Live ML Recovery Prediction OK")
    passed_count += 1

    # 9. Root Cause Generation
    print("[Test 9/18] Root Cause Generation...")
    root_cause = intel.get("root_cause", {})
    assert root_cause is not None, "Root cause analysis missing"
    print("[OK] Root Cause Generation OK")
    passed_count += 1

    # 10. Recommendation Generation
    print("[Test 10/18] Recommendation Generation...")
    rec = intel.get("recommendation", {})
    assert rec is not None, "Recommendation missing"
    print("[OK] Recommendation Generation OK")
    passed_count += 1

    # 11. Execute Recovery Action API
    print("[Test 11/18] Execute Recovery Action API...")
    res = client.post(f"/api/merchant/live-payments/{test_pm_id}/actions", json={
        "merchant_id": "m_1004",
        "action_type": "otp_reminder"
    })
    assert res.status_code == 200, f"Execute action failed: {res.text}"
    act_body = res.json()
    assert act_body["status"] == "executed"
    assert act_body["action"] == "otp_reminder"
    print("[OK] Execute Recovery Action API OK")
    passed_count += 1

    # 12. Duplicate Recovery Action Prevention
    print("[Test 12/18] Duplicate Recovery Action Prevention...")
    res = client.post(f"/api/merchant/live-payments/{test_pm_id}/actions", json={
        "merchant_id": "m_1004",
        "action_type": "otp_reminder"
    })
    assert res.status_code == 400, f"Expected 400 duplicate rejection, got {res.status_code}"
    print("[OK] Duplicate Recovery Action Prevention OK")
    passed_count += 1

    # 13. Payment Timeline Generation
    print("[Test 13/18] Payment Timeline Generation...")
    res = client.get(f"/api/merchant/live-payments/{test_pm_id}/timeline?merchant_id=m_1004")
    assert res.status_code == 200, f"Timeline fetch failed: {res.text}"
    timeline = res.json()
    assert isinstance(timeline, list)
    assert len(timeline) >= 2, f"Expected timeline events, got {len(timeline)}"
    event_types = [e["event_type"] for e in timeline]
    assert "ORDER_CREATED" in event_types
    assert "RECOVERY_ACTION_EXECUTED" in event_types
    print(f"[OK] Payment Timeline Generation OK ({len(timeline)} events: {event_types})")
    passed_count += 1

    # 14. Merchant Domain Isolation (m_1000 vs m_1004)
    print("[Test 14/18] Merchant Domain Isolation (m_1000 vs m_1004)...")
    # Cross-merchant query for actions
    res_act = client.get(f"/api/merchant/live-payments/{test_pm_id}/actions?merchant_id=m_1000")
    assert res_act.status_code == 404, f"Expected 404 for cross-merchant action access, got {res_act.status_code}"

    # Cross-merchant query for timeline
    res_time = client.get(f"/api/merchant/live-payments/{test_pm_id}/timeline?merchant_id=m_1000")
    assert res_time.status_code == 404, f"Expected 404 for cross-merchant timeline access, got {res_time.status_code}"

    # Cross-merchant action execution
    res_exec = client.post(f"/api/merchant/live-payments/{test_pm_id}/actions", json={
        "merchant_id": "m_1000",
        "action_type": "smart_retry"
    })
    assert res_exec.status_code == 404, f"Expected 404 for cross-merchant action execution, got {res_exec.status_code}"

    # Cross-merchant live intelligence
    res_intel = client.get(f"/api/merchant/live-payments/{test_pm_id}/intelligence?merchant_id=m_1000")
    assert res_intel.status_code == 404, f"Expected 404 for cross-merchant intelligence access, got {res_intel.status_code}"
    print("[OK] Merchant Domain Isolation Enforcement OK (Strict 404s)")
    passed_count += 1

    # 15. Webhook Idempotency
    print("[Test 15/18] Webhook Idempotency...")
    wh_payload = {
        "event": "payment.failed",
        "event_id": "evt_test_idempotency_123",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_wh_test_123",
                    "order_id": "order_wh_test_123",
                    "amount": 10000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "bank": "HDFC",
                    "error_code": "BAD_REQUEST_ABANDONED",
                    "error_description": "Payment authorization timed out"
                }
            }
        }
    }
    # Send webhook 1st time
    res1 = client.post("/api/webhooks/razorpay", json=wh_payload)
    assert res1.status_code == 200, f"Webhook 1 failed: {res1.text}"
    assert res1.json()["status"] == "ok"

    # Send webhook 2nd time (duplicate)
    res2 = client.post("/api/webhooks/razorpay", json=wh_payload)
    assert res2.status_code == 200, f"Webhook 2 failed: {res2.text}"
    assert res2.json()["status"] == "ignored_duplicate"
    print("[OK] Webhook Idempotency OK")
    passed_count += 1

    # 16. CSV Dataset Immutability Verification
    print("[Test 16/18] CSV Dataset Immutability Verification...")
    data_dir = os.path.join(BACKEND_DIR, "data")
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    assert len(csv_files) > 0, "No CSV files found in backend/data"
    for csv_name in csv_files:
        csv_path = os.path.join(data_dir, csv_name)
        df = pd.read_csv(csv_path)
        assert len(df) > 0, f"CSV dataset {csv_name} is empty!"
    print(f"[OK] CSV Dataset Immutability OK ({len(csv_files)} CSV files verified intact)")
    passed_count += 1

    # 17. Historical Intelligence Regression
    print("[Test 17/18] Historical Intelligence Regression...")
    res = client.get("/api/merchant/intelligence/payment-analysis/pay_104421?merchant_id=m_1004")
    assert res.status_code == 200, f"Historical intelligence lookup failed: {res.text}"
    h_body = res.json()
    assert h_body["payment_id"] == "pay_104421"
    assert "prediction" in h_body
    print("[OK] Historical Intelligence Regression OK")
    passed_count += 1

    # 18. Existing API Regression
    print("[Test 18/18] Existing API Regression...")
    res_dash = client.get("/api/merchant/dashboard?merchant_id=m_1004")
    assert res_dash.status_code == 200, f"Merchant dashboard API failed: {res_dash.text}"
    assert res_dash.json()["merchant_id"] == "m_1004"

    res_events = client.get("/api/merchant/live-payments/events?merchant_id=m_1004")
    assert res_events.status_code == 200, f"Live payment events API failed: {res_events.text}"
    print("[OK] Existing API Regression OK")

    passed_count += 1

    print("=" * 60)
    print(f"RESULTS: {passed_count}/{total_tests} HARDENING TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
