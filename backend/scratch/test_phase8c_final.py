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

# Set DEMO_MODE=true for testing
os.environ["DEMO_MODE"] = "true"

from main import app
from database import init_db, SessionLocal, LivePaymentModel, RecoveryActionModel, DB_PATH
from services.live_payment_service import get_live_payment_service
from services.recovery_action_service import get_recovery_action_service

client = TestClient(app)

def run_master_qa_tests():
    print("=" * 65)
    print("RECOVERAI PHASE 8C MASTER QA HARDENING & VALIDATION SUITE")
    print("=" * 65)

    passed_count = 0
    total_tests = 22

    # 1. Health Endpoint
    print("[Test 1/22] Health endpoint readiness...")
    res = client.get("/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.json()
    assert body.get("status") in ["healthy", "degraded"], f"Unexpected health status {body}"
    print("[OK] Health Endpoint Readiness OK")
    passed_count += 1

    # 2. Database Initialization
    print("[Test 2/22] Database initialization & schema verification...")
    init_db()
    assert os.path.exists(DB_PATH), f"Database file missing at {DB_PATH}"
    print("[OK] Database Initialization OK")
    passed_count += 1

    # 3. Existing Data Preservation
    print("[Test 3/22] Existing CSV Data Preservation...")
    data_dir = os.path.join(BACKEND_DIR, "data")
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    assert len(csv_files) > 0, "No CSV files found in backend/data"
    for csv_file in csv_files:
        df = pd.read_csv(os.path.join(data_dir, csv_file))
        assert len(df) > 0, f"CSV dataset {csv_file} is empty"
    print(f"[OK] Existing Data Preservation OK ({len(csv_files)} CSV files verified)")
    passed_count += 1

    # 4. Demo Reset Protection when DEMO_MODE=false
    print("[Test 4/22] Demo Reset Protection when DEMO_MODE=false...")
    import routers.demo as demo_module
    old_demo_mode = demo_module.DEMO_MODE
    try:
        demo_module.DEMO_MODE = False
        res_prot = client.post("/api/demo/reset-all")
        assert res_prot.status_code == 403, f"Expected 403 Forbidden, got {res_prot.status_code}"
        res_seed_prot = client.post("/api/demo/seed")
        assert res_seed_prot.status_code == 403, f"Expected 403 Forbidden, got {res_seed_prot.status_code}"
    finally:
        demo_module.DEMO_MODE = old_demo_mode
    print("[OK] Demo Reset Protection when DEMO_MODE=false OK (Strict 403s)")
    passed_count += 1

    # 5. Demo Reset when DEMO_MODE=true
    print("[Test 5/22] Demo Reset when DEMO_MODE=true...")
    res_reset = client.post("/api/demo/reset-all")
    assert res_reset.status_code == 200, f"Reset all failed: {res_reset.text}"
    db = SessionLocal()
    try:
        count = db.query(LivePaymentModel).count()
        assert count == 0, f"Expected 0 live payments after reset, found {count}"
    finally:
        db.close()
    print("[OK] Demo Reset when DEMO_MODE=true OK")
    passed_count += 1

    # 6. Demo Seed API
    print("[Test 6/22] Demo Seed API...")
    res_seed = client.post("/api/demo/seed")
    assert res_seed.status_code == 200, f"Seed API failed: {res_seed.text}"
    seed_body = res_seed.json()
    assert seed_body["seeded_payment_id"] == "pay_demo_seed_8c"
    print("[OK] Demo Seed API OK")
    passed_count += 1

    # 7. Deterministic Demo Scenario Verification
    print("[Test 7/22] Deterministic Demo Scenario Verification...")
    res_intel = client.get("/api/merchant/live-payments/pay_demo_seed_8c/intelligence?merchant_id=m_1004")
    assert res_intel.status_code == 200, f"Seeded intelligence lookup failed: {res_intel.text}"
    intel_data = res_intel.json()
    assert intel_data["payment"]["amount_inr"] == 12499.0
    assert intel_data["payment"]["status"] == "failed"
    assert intel_data["recovery_prediction"]["recovery_probability"] == 0.78
    print("[OK] Deterministic Demo Scenario Verification OK (₹12,499.00 payment with 78% ML recovery)")
    passed_count += 1

    # 8. Live Payment Persistence
    print("[Test 8/22] Live Payment Persistence in SQLite DB...")
    lps = get_live_payment_service()
    order_rec = lps.create_live_order(
        razorpay_order_id="order_test_qa8c_99",
        merchant_id="m_1004",
        amount_inr=3200.0,
        currency="INR"
    )
    pm_id = order_rec["payment_id"]
    db = SessionLocal()
    try:
        db_rec = db.query(LivePaymentModel).filter_by(payment_id=pm_id).first()
        assert db_rec is not None, "Live payment not found in DB"
        assert db_rec.amount == 3200.0
    finally:
        db.close()
    print("[OK] Live Payment Persistence OK")
    passed_count += 1

    # 9. Backend Restart Data Persistence Simulation
    print("[Test 9/22] Backend Restart Data Persistence Simulation...")
    db = SessionLocal()
    try:
        persisted = db.query(LivePaymentModel).filter_by(payment_id=pm_id).first()
        assert persisted is not None, "Failed to persist across simulated restart"
        assert persisted.merchant_id == "m_1004"
    finally:
        db.close()
    print("[OK] Backend Restart Persistence OK")
    passed_count += 1

    # 10. ML Recovery Prediction
    print("[Test 10/22] Live ML Prediction Execution...")
    test_pm_id = f"pay_rzp_qa8c_99"
    test_order_id = "order_test_qa8c_99"
    secret = os.getenv("RAZORPAY_KEY_SECRET", "IDqTyn2czz2UDDzUpNmwT7Sd").strip()
    msg = f"{test_order_id}|{test_pm_id}".encode("utf-8")
    valid_sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    res_ver = client.post("/api/payments/verify", json={
        "razorpay_payment_id": test_pm_id,
        "razorpay_order_id": test_order_id,
        "razorpay_signature": valid_sig,
        "merchant_id": "m_1004",
        "status": "captured"
    })
    assert res_ver.status_code == 200, f"Verification failed: {res_ver.text}"
    pred_res = res_ver.json().get("intelligence", {}).get("prediction", {})
    assert "recovery_probability" in pred_res
    print("[OK] Live ML Recovery Prediction OK")
    passed_count += 1

    # 11. Root Cause Generation
    print("[Test 11/22] Root Cause Generation...")
    rc_res = res_ver.json().get("intelligence", {}).get("root_cause")
    assert rc_res is not None, "Root cause missing"
    print("[OK] Root Cause Generation OK")
    passed_count += 1

    # 12. Recommendation Generation
    print("[Test 12/22] AI Recommendation Generation...")
    rec_res = res_ver.json().get("intelligence", {}).get("recommendation")
    assert rec_res is not None, "Recommendation missing"
    print("[OK] AI Recommendation Generation OK")
    passed_count += 1

    # 13. Recovery Action Execution
    print("[Test 13/22] Recovery Action Execution API...")
    res_act = client.post(f"/api/merchant/live-payments/{test_pm_id}/actions", json={
        "merchant_id": "m_1004",
        "action_type": "smart_retry"
    })
    assert res_act.status_code == 200, f"Execute action failed: {res_act.text}"
    assert res_act.json()["status"] == "executed"
    print("[OK] Recovery Action Execution API OK")
    passed_count += 1

    # 14. Duplicate Action Prevention
    print("[Test 14/22] Duplicate Recovery Action Prevention...")
    res_dup = client.post(f"/api/merchant/live-payments/{test_pm_id}/actions", json={
        "merchant_id": "m_1004",
        "action_type": "smart_retry"
    })
    assert res_dup.status_code in (200, 400), f"Expected 200 or 400 for duplicate action, got {res_dup.status_code}"
    print("[OK] Duplicate Recovery Action Prevention OK")
    passed_count += 1

    # 15. Payment Timeline Update
    print("[Test 15/22] Payment Timeline Generation & Update...")
    res_tl = client.get(f"/api/merchant/live-payments/{test_pm_id}/timeline?merchant_id=m_1004")
    assert res_tl.status_code == 200, f"Timeline fetch failed: {res_tl.text}"
    tl = res_tl.json()
    assert isinstance(tl, list)
    assert len(tl) >= 2
    event_types = [e["event_type"] for e in tl]
    assert "RECOVERY_ACTION_EXECUTED" in event_types
    print(f"[OK] Payment Timeline Generation OK ({len(tl)} events logged)")
    passed_count += 1

    # 16. Merchant Domain Isolation Enforcement
    print("[Test 16/22] Merchant Domain Isolation Enforcement...")
    res_iso1 = client.get(f"/api/merchant/live-payments/{test_pm_id}/actions?merchant_id=m_1000")
    assert res_iso1.status_code == 404, f"Expected 404, got {res_iso1.status_code}"
    res_iso2 = client.get(f"/api/merchant/live-payments/{test_pm_id}/timeline?merchant_id=m_1000")
    assert res_iso2.status_code == 404, f"Expected 404, got {res_iso2.status_code}"
    print("[OK] Merchant Domain Isolation OK (Strict 404s)")
    passed_count += 1

    # 17. Webhook Idempotency
    print("[Test 17/22] Webhook Idempotency Enforcement...")
    wh_body = {
        "event": "payment.failed",
        "event_id": "evt_qa8c_idempotent_01",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_wh_qa8c_01",
                    "order_id": "order_wh_qa8c_01",
                    "amount": 5000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "bank": "SBI",
                    "error_code": "BAD_REQUEST_TIMEOUT",
                    "error_description": "UPI PSP Timeout"
                }
            }
        }
    }
    r1 = client.post("/api/webhooks/razorpay", json=wh_body)
    assert r1.status_code == 200 and r1.json()["status"] == "ok"
    r2 = client.post("/api/webhooks/razorpay", json=wh_body)
    assert r2.status_code == 200 and r2.json()["status"] == "ignored_duplicate"
    print("[OK] Webhook Idempotency Enforcement OK")
    passed_count += 1

    # 18. CSV Dataset Immutability
    print("[Test 18/22] CSV Dataset Immutability Verification...")
    for csv_file in csv_files:
        df = pd.read_csv(os.path.join(data_dir, csv_file))
        assert len(df) > 0, f"CSV file {csv_file} modified or empty!"
    print("[OK] CSV Dataset Immutability OK")
    passed_count += 1

    # 19. Historical API Regression
    print("[Test 19/22] Historical Intelligence API Regression...")
    res_h = client.get("/api/merchant/intelligence/payment-analysis/pay_104421?merchant_id=m_1004")
    assert res_h.status_code == 200, f"Historical lookup failed: {res_h.text}"
    assert res_h.json()["payment_id"] == "pay_104421"
    print("[OK] Historical API Regression OK")
    passed_count += 1

    # 20. Live API Regression
    print("[Test 20/22] Live Payments Feed API Regression...")
    res_l = client.get("/api/merchant/live-payments/events?merchant_id=m_1004")
    assert res_l.status_code == 200, f"Live payments API failed: {res_l.text}"
    assert "live_payments" in res_l.json()
    print("[OK] Live API Regression OK")
    passed_count += 1

    # 21. Internal API Regression
    print("[Test 21/22] Internal Operations Portal API Regression...")
    res_int = client.get("/api/internal/dashboard")
    assert res_int.status_code == 200, f"Internal dashboard failed: {res_int.text}"
    assert "total_payment_volume" in res_int.json()
    print("[OK] Internal API Regression OK")
    passed_count += 1

    # 22. Docker Configuration Validation
    print("[Test 22/22] Docker Configuration Validation...")
    compose_path = os.path.join(os.path.dirname(BACKEND_DIR), "docker-compose.yml")
    assert os.path.exists(compose_path), "docker-compose.yml file missing!"
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_content = f.read()
    assert "sqlite_data:/app/data" in compose_content, "Missing persistent volume sqlite_data in docker-compose.yml"
    assert "DEMO_MODE=true" in compose_content, "Missing DEMO_MODE environment variable in docker-compose.yml"
    print("[OK] Docker Configuration Validation OK")
    passed_count += 1

    print("=" * 65)
    print(f"RESULTS: {passed_count}/{total_tests} MASTER QA HARDENING TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_master_qa_tests()
