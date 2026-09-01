import sys
import os
from datetime import datetime

# Ensure backend path is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db, SessionLocal, LivePaymentModel, RecoveryActionModel, InfrastructureIncidentModel
from services.merchant_service import MerchantService

def test_merchant_dashboard_dynamic_suite():
    print("=" * 70)
    print("RECOVERAI QA SUITE: DYNAMIC MERCHANT DASHBOARD SINGLE SOURCE OF TRUTH")
    print("=" * 70)

    init_db()
    merchant_service = MerchantService()
    test_merchant_id = "m_1004"

    # Helper function to clear live DB records before each test
    def clear_db():
        db = SessionLocal()
        try:
            db.query(RecoveryActionModel).delete()
            db.query(InfrastructureIncidentModel).delete()
            db.query(LivePaymentModel).delete()
            db.commit()
        finally:
            db.close()

    # ----------------------------------------------------
    # TEST 1: Zero transactions / Empty DB
    # ----------------------------------------------------
    print("\n[Test 1/9] Zero transactions / Empty DB state...")
    clear_db()
    dash = merchant_service.get_dashboard(test_merchant_id)
    assert dash is not None, "Expected dashboard data dict"
    assert dash["failed_payments"] == 0, f"Expected 0 failed, got {dash['failed_payments']}"
    assert dash["revenue_at_risk"] == 0.0, f"Expected 0.0 risk, got {dash['revenue_at_risk']}"
    assert dash["revenue_recovered"] == 0.0, f"Expected 0.0 recovered, got {dash['revenue_recovered']}"
    assert dash["recovery_rate"] == 0.0, f"Expected 0.0 rate, got {dash['recovery_rate']}"
    assert dash["active_recovery_cases"] == 0, f"Expected 0 active cases, got {dash['active_recovery_cases']}"
    print("[OK] Test 1 Passed: Empty database displays exact 0 metrics without error.")

    # ----------------------------------------------------
    # TEST 2: Single failed payment (INR 1,234)
    # ----------------------------------------------------
    print("\n[Test 2/9] Single failed payment (INR 1,234)...")
    clear_db()
    db = SessionLocal()
    try:
        p1 = LivePaymentModel(
            payment_id="pay_test_m1_1234",
            order_id="order_test_m1_1234",
            merchant_id=test_merchant_id,
            amount=1234.0,
            currency="INR",
            status="failed",
            error_code="BAD_REQUEST_TIMEOUT",
            bank="HDFC Bank"
        )
        db.add(p1)
        db.commit()
    finally:
        db.close()

    dash = merchant_service.get_dashboard(test_merchant_id)
    assert dash["failed_payments"] == 1, f"Expected 1 failed payment, got {dash['failed_payments']}"
    assert dash["revenue_at_risk"] == 1234.0, f"Expected 1234.0 at risk, got {dash['revenue_at_risk']}"
    assert dash["revenue_recovered"] == 0.0
    assert dash["recovery_rate"] == 0.0
    assert dash["active_recovery_cases"] == 1, f"Expected 1 active case, got {dash['active_recovery_cases']}"
    print("[OK] Test 2 Passed: Single failed payment (INR 1,234) calculated risk=1234.0 and 1 active case.")

    # ----------------------------------------------------
    # TEST 3: Multiple failed payments aggregation
    # ----------------------------------------------------
    print("\n[Test 3/9] Multiple failed payments aggregation...")
    clear_db()
    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_test_m3_1", order_id="order_test_m3_1", merchant_id=test_merchant_id,
            amount=1000.0, currency="INR", status="failed", bank="SBI"
        ))
        db.add(LivePaymentModel(
            payment_id="pay_test_m3_2", order_id="order_test_m3_2", merchant_id=test_merchant_id,
            amount=2500.0, currency="INR", status="failed", bank="SBI"
        ))
        db.commit()
    finally:
        db.close()

    dash = merchant_service.get_dashboard(test_merchant_id)
    assert dash["failed_payments"] == 2, f"Expected 2 failed payments, got {dash['failed_payments']}"
    assert dash["revenue_at_risk"] == 3500.0, f"Expected 3500.0 at risk, got {dash['revenue_at_risk']}"
    assert dash["active_recovery_cases"] == 2, f"Expected 2 active cases, got {dash['active_recovery_cases']}"
    print("[OK] Test 3 Passed: Multiple failed payments aggregated to INR 3,500.00 across 2 cases.")

    # ----------------------------------------------------
    # TEST 4: Single captured/verified payment
    # ----------------------------------------------------
    print("\n[Test 4/9] Captured/Verified payment...")
    clear_db()
    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_test_m4_captured", order_id="order_test_m4_captured", merchant_id=test_merchant_id,
            amount=5000.0, currency="INR", status="captured", bank="Razorpay Gateway"
        ))
        db.commit()
    finally:
        db.close()

    dash = merchant_service.get_dashboard(test_merchant_id)
    assert dash["failed_payments"] == 0
    assert dash["successful_payments"] == 1
    assert dash["revenue_at_risk"] == 0.0
    assert dash["revenue_recovered"] == 5000.0, f"Expected 5000.0 recovered, got {dash['revenue_recovered']}"
    assert dash["recovery_rate"] == 100.0
    assert dash["active_recovery_cases"] == 0
    print("[OK] Test 4 Passed: Captured payment updated revenue_recovered=5000.0 and recovery_rate=100.0%.")

    # ----------------------------------------------------
    # TEST 5: Failed + Captured combination split
    # ----------------------------------------------------
    print("\n[Test 5/9] Failed + Captured combination split...")
    clear_db()
    db = SessionLocal()
    try:
        # Failed INR 12,499 + Captured INR 1,234
        db.add(LivePaymentModel(
            payment_id="pay_test_m5_fail", order_id="order_test_m5_fail", merchant_id=test_merchant_id,
            amount=12499.0, currency="INR", status="failed", bank="HDFC Bank"
        ))
        db.add(LivePaymentModel(
            payment_id="pay_test_m5_succ", order_id="order_test_m5_succ", merchant_id=test_merchant_id,
            amount=1234.0, currency="INR", status="captured", bank="Razorpay Gateway"
        ))
        db.commit()
    finally:
        db.close()

    dash = merchant_service.get_dashboard(test_merchant_id)
    assert dash["failed_payments"] == 1
    assert dash["successful_payments"] == 1
    assert dash["revenue_at_risk"] == 12499.0, f"Expected 12499.0 risk, got {dash['revenue_at_risk']}"
    assert dash["revenue_recovered"] == 1234.0, f"Expected 1234.0 recovered, got {dash['revenue_recovered']}"
    expected_rate = round((1234.0 / (12499.0 + 1234.0) * 100), 2)
    assert dash["recovery_rate"] == expected_rate, f"Expected rate {expected_rate}%, got {dash['recovery_rate']}%"
    print(f"[OK] Test 5 Passed: Combination split verified (Risk: INR 12,499, Recovered: INR 1,234, Rate: {dash['recovery_rate']}%).")

    # ----------------------------------------------------
    # TEST 6: Recovery action execution transition
    # ----------------------------------------------------
    print("\n[Test 6/9] Recovery action execution transition...")
    clear_db()
    db = SessionLocal()
    try:
        # Failed payment INR 2000 + executed recovery action
        p6 = LivePaymentModel(
            payment_id="pay_test_m6_act", order_id="order_test_m6_act", merchant_id=test_merchant_id,
            amount=2000.0, currency="INR", status="failed", bank="ICICI UPI"
        )
        act = RecoveryActionModel(
            payment_id="pay_test_m6_act", merchant_id=test_merchant_id,
            action_type="smart_retry", status="executed"
        )
        db.add_all([p6, act])
        db.commit()
    finally:
        db.close()

    dash = merchant_service.get_dashboard(test_merchant_id)
    assert dash["revenue_recovered"] == 2000.0, f"Expected 2000.0 recovered, got {dash['revenue_recovered']}"
    assert dash["active_recovery_cases"] == 0, f"Expected 0 active cases, got {dash['active_recovery_cases']}"
    print("[OK] Test 6 Passed: Executed recovery action transitioned INR 2,000 to recovered and decremented active cases.")

    # ----------------------------------------------------
    # TEST 7: Dashboard API Response Verification via TestClient
    # ----------------------------------------------------
    print("\n[Test 7/9] FastAPI endpoints GET /api/merchant/dashboard & GET /api/merchant/metrics...")
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)

    res_dash = client.get(f"/api/merchant/dashboard?merchant_id={test_merchant_id}")
    assert res_dash.status_code == 200, f"Expected 200, got {res_dash.status_code}"
    dash_json = res_dash.json()
    assert "revenue_at_risk" in dash_json
    assert "failed_payments" in dash_json
    assert "revenue_recovered" in dash_json
    assert "recovery_rate" in dash_json

    res_met = client.get(f"/api/merchant/metrics?merchant_id={test_merchant_id}")
    assert res_met.status_code == 200, f"Expected 200, got {res_met.status_code}"
    met_json = res_met.json()
    assert met_json["merchant_id"] == test_merchant_id
    print("[OK] Test 7 Passed: Both /api/merchant/dashboard and /api/merchant/metrics returned structured JSON.")

    # ----------------------------------------------------
    # TEST 8: Amount aggregation accuracy
    # ----------------------------------------------------
    print("\n[Test 8/9] Amount aggregation accuracy...")
    clear_db()
    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_test_m8_1", order_id="order_test_m8_1", merchant_id=test_merchant_id,
            amount=123456.78, currency="INR", status="failed", bank="SBI"
        ))
        db.commit()
    finally:
        db.close()

    dash = merchant_service.get_dashboard(test_merchant_id)
    assert dash["revenue_at_risk"] == 123456.78, f"Expected 123456.78, got {dash['revenue_at_risk']}"
    print("[OK] Test 8 Passed: Amount INR 1,23456.78 aggregated with exact decimal precision.")

    # ----------------------------------------------------
    # TEST 9: Persistence after service re-instantiation
    # ----------------------------------------------------
    print("\n[Test 9/9] Persistence after service re-instantiation...")
    new_service = MerchantService()
    dash_reinst = new_service.get_dashboard(test_merchant_id)
    assert dash_reinst["revenue_at_risk"] == 123456.78
    assert dash_reinst["failed_payments"] == 1
    print("[OK] Test 9 Passed: Dashboard metrics persisted cleanly across service re-instantiations.")

    clear_db()
    print("=" * 70)
    print("ALL 9 MERCHANT DASHBOARD SINGLE SOURCE OF TRUTH TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_merchant_dashboard_dynamic_suite()
