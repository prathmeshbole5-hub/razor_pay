import sys
import os
from datetime import datetime

# Ensure backend path is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db, SessionLocal, LivePaymentModel, InfrastructureIncidentModel
from services.internal_service import InternalService, GATEWAY_HEALTH_THRESHOLDS, normalize_gateway_name

def test_dynamic_gateway_health_suite():
    print("=" * 70)
    print("RECOVERAI QA SUITE: DYNAMIC GATEWAY & BANK HEALTH AGGREGATION")
    print("=" * 70)

    init_db()
    internal_service = InternalService()

    # Helper function to clear live DB records before each test
    def clear_db():
        db = SessionLocal()
        try:
            db.query(InfrastructureIncidentModel).delete()
            db.query(LivePaymentModel).delete()
            db.commit()
        finally:
            db.close()

    # ----------------------------------------------------
    # TEST H: Empty transaction dataset handling
    # ----------------------------------------------------
    print("\n[Test H] Empty transaction dataset handling...")
    clear_db()
    health_data = internal_service.get_gateway_health()
    assert isinstance(health_data, list), "Expected list response for gateway health"
    assert len(health_data) >= 5, f"Expected standard 5 gateways, got {len(health_data)}"
    for gw in health_data:
        assert "gateway" in gw
        assert "current_status" in gw
        assert "failure_rate" in gw
        assert "recent_failure_count" in gw
        assert "amount_at_risk" in gw
    print("[OK] Test H Passed: Empty database handled gracefully with standard structure.")

    # ----------------------------------------------------
    # TEST A: No failures -> HEALTHY
    # ----------------------------------------------------
    print("\n[Test A] No failures -> HEALTHY status...")
    clear_db()
    db = SessionLocal()
    try:
        # Add successful payments for Razorpay Gateway
        p1 = LivePaymentModel(
            payment_id="pay_test_a1",
            order_id="order_test_a1",
            merchant_id="m_1004",
            amount=1000.0,
            currency="INR",
            status="captured",
            payment_method="Card",
            bank="Razorpay Gateway"
        )
        p2 = LivePaymentModel(
            payment_id="pay_test_a2",
            order_id="order_test_a2",
            merchant_id="m_1004",
            amount=2000.0,
            currency="INR",
            status="verified",
            payment_method="UPI",
            bank="Razorpay Gateway"
        )
        db.add_all([p1, p2])
        db.commit()
    finally:
        db.close()

    health_data = internal_service.get_gateway_health()
    rzp_gw = next((g for g in health_data if g["gateway"] == "Razorpay Gateway"), None)
    assert rzp_gw is not None, "Razorpay Gateway not found"
    assert rzp_gw["recent_failure_count"] == 0, f"Expected 0 recent failures, got {rzp_gw['recent_failure_count']}"
    assert rzp_gw["current_status"] == "HEALTHY", f"Expected HEALTHY, got {rzp_gw['current_status']}"
    print(f"[OK] Test A Passed: Razorpay Gateway status is {rzp_gw['current_status']} with 0 failures.")

    # ----------------------------------------------------
    # TEST B: Small number of failures below threshold -> HEALTHY / DEGRADED according to threshold
    # ----------------------------------------------------
    print("\n[Test B] Small number of failures below threshold...")
    clear_db()
    db = SessionLocal()
    try:
        # Add 19 successful payments + 1 failure for Razorpay Gateway (failure_rate = 5%, recent_failures = 1)
        for i in range(19):
            db.add(LivePaymentModel(
                payment_id=f"pay_test_b_succ_{i}",
                order_id=f"order_test_b_succ_{i}",
                merchant_id="m_1004",
                amount=1000.0,
                currency="INR",
                status="captured",
                payment_method="Card",
                bank="Razorpay Gateway"
            ))
        p_fail = LivePaymentModel(
            payment_id="pay_test_b_fail",
            order_id="order_test_b_fail",
            merchant_id="m_1004",
            amount=500.0,
            currency="INR",
            status="failed",
            error_code="card_declined",
            payment_method="Card",
            bank="Razorpay Gateway"
        )
        db.add(p_fail)
        db.commit()
    finally:
        db.close()

    health_data = internal_service.get_gateway_health()
    rzp_gw = next((g for g in health_data if g["gateway"] == "Razorpay Gateway"), None)
    assert rzp_gw["recent_failure_count"] == 1
    assert rzp_gw["failure_rate"] == 5.0, f"Expected 5.0% failure rate, got {rzp_gw['failure_rate']}%"
    assert rzp_gw["current_status"] in ["HEALTHY", "DEGRADED"]
    print(f"[OK] Test B Passed: 1 failure (5% failure rate) calculated status={rzp_gw['current_status']} correctly.")

    # ----------------------------------------------------
    # TEST C: Repeated failures -> DEGRADED
    # ----------------------------------------------------
    print("\n[Test C] Repeated failures meeting degraded threshold -> DEGRADED status...")
    clear_db()
    db = SessionLocal()
    try:
        # Add 12 successful payments + 3 failed payments for HDFC Gateway (failure_rate = 20.0%, recent_failures = 3)
        for i in range(12):
            db.add(LivePaymentModel(
                payment_id=f"pay_test_c_succ_{i}",
                order_id=f"order_test_c_succ_{i}",
                merchant_id="m_1004",
                amount=1000.0,
                currency="INR",
                status="captured",
                payment_method="Card",
                bank="HDFC Bank"
            ))
        for i in range(3):
            db.add(LivePaymentModel(
                payment_id=f"pay_test_c_fail_{i}",
                order_id=f"order_test_c_fail_{i}",
                merchant_id="m_1004",
                amount=1500.0,
                currency="INR",
                status="failed",
                error_code="BAD_REQUEST_TIMEOUT",
                error_description="HDFC Gateway Timeout",
                payment_method="Card",
                bank="HDFC Bank"
            ))
        db.commit()
    finally:
        db.close()

    health_data = internal_service.get_gateway_health()
    hdfc_gw = next((g for g in health_data if g["gateway"] == "HDFC Gateway"), None)
    assert hdfc_gw is not None, "HDFC Gateway not found"
    assert hdfc_gw["recent_failure_count"] == 3, f"Expected 3 recent failures, got {hdfc_gw['recent_failure_count']}"
    assert hdfc_gw["current_status"] == "DEGRADED", f"Expected DEGRADED, got {hdfc_gw['current_status']}"
    print(f"[OK] Test C Passed: HDFC Gateway with 3 failures transitioned to {hdfc_gw['current_status']}.")

    # ----------------------------------------------------
    # TEST D: Severe failure spike -> OUTAGE
    # ----------------------------------------------------
    print("\n[Test D] Severe failure spike -> OUTAGE status...")
    clear_db()
    db = SessionLocal()
    try:
        # Add 8 failed payments for SBI Card Gateway (meets OUTAGE threshold of recent_failures >= 8)
        for i in range(8):
            db.add(LivePaymentModel(
                payment_id=f"pay_test_d_{i}",
                order_id=f"order_test_d_{i}",
                merchant_id="m_1004",
                amount=2500.0,
                currency="INR",
                status="failed",
                error_code="international_transaction_not_allowed",
                error_description="SBI Card international restriction spike",
                payment_method="Card",
                bank="SBI"
            ))
        db.commit()
    finally:
        db.close()

    health_data = internal_service.get_gateway_health()
    sbi_gw = next((g for g in health_data if g["gateway"] == "SBI Card Gateway"), None)
    assert sbi_gw is not None, "SBI Card Gateway not found"
    assert sbi_gw["recent_failure_count"] == 8, f"Expected 8 recent failures, got {sbi_gw['recent_failure_count']}"
    assert sbi_gw["current_status"] == "OUTAGE", f"Expected OUTAGE, got {sbi_gw['current_status']}"
    print(f"[OK] Test D Passed: SBI Card Gateway severe failure spike resulted in {sbi_gw['current_status']}.")

    # ----------------------------------------------------
    # TEST E: Correct amount-at-risk calculation
    # ----------------------------------------------------
    print("\n[Test E] Correct amount-at-risk calculation...")
    clear_db()
    db = SessionLocal()
    try:
        # Add 2 failures: ₹1000 + ₹2500 = ₹3500
        db.add(LivePaymentModel(
            payment_id="pay_test_e1", order_id="order_test_e1", merchant_id="m_1004",
            amount=1000.0, currency="INR", status="failed", bank="SBI"
        ))
        db.add(LivePaymentModel(
            payment_id="pay_test_e2", order_id="order_test_e2", merchant_id="m_1004",
            amount=2500.0, currency="INR", status="failed", bank="SBI"
        ))
        db.commit()
    finally:
        db.close()

    health_data = internal_service.get_gateway_health()
    sbi_gw = next((g for g in health_data if g["gateway"] == "SBI Card Gateway"), None)
    assert sbi_gw["amount_at_risk"] == 3500.0, f"Expected INR 3500.0 at risk, got INR {sbi_gw['amount_at_risk']}"
    print(f"[OK] Test E Passed: Correct amount at risk calculated (INR {sbi_gw['amount_at_risk']:,.2f}).")

    # ----------------------------------------------------
    # TEST F: Correct impacted merchant count
    # ----------------------------------------------------
    print("\n[Test F] Correct impacted merchant count...")
    clear_db()
    db = SessionLocal()
    try:
        # Failures across 2 distinct merchants: m_1004 and m_1001
        db.add(LivePaymentModel(
            payment_id="pay_test_f1", order_id="order_test_f1", merchant_id="m_1004",
            amount=1200.0, currency="INR", status="failed", bank="ICICI UPI"
        ))
        db.add(LivePaymentModel(
            payment_id="pay_test_f2", order_id="order_test_f2", merchant_id="m_1001",
            amount=800.0, currency="INR", status="failed", bank="ICICI UPI"
        ))
        db.commit()
    finally:
        db.close()

    health_data = internal_service.get_gateway_health()
    icici_gw = next((g for g in health_data if g["gateway"] == "ICICI UPI"), None)
    assert icici_gw["impacted_merchants"] == 2, f"Expected 2 impacted merchants, got {icici_gw['impacted_merchants']}"
    print(f"[OK] Test F Passed: Impacted merchant count is {icici_gw['impacted_merchants']}.")

    # ----------------------------------------------------
    # TEST G: Correct gateway association
    # ----------------------------------------------------
    print("\n[Test G] Correct gateway association...")
    clear_db()
    db = SessionLocal()
    try:
        # Fail an SBI payment and verify Axis Wallet remains unaffected
        db.add(LivePaymentModel(
            payment_id="pay_test_g_sbi", order_id="order_test_g_sbi", merchant_id="m_1004",
            amount=1000.0, currency="INR", status="failed", bank="SBI", error_code="international_transaction_not_allowed"
        ))
        db.commit()
    finally:
        db.close()

    health_data = internal_service.get_gateway_health()
    sbi_gw = next((g for g in health_data if g["gateway"] == "SBI Card Gateway"), None)
    axis_gw = next((g for g in health_data if g["gateway"] == "Axis Wallet"), None)

    assert sbi_gw["recent_failure_count"] == 1, f"Expected SBI failures = 1, got {sbi_gw['recent_failure_count']}"
    assert axis_gw["recent_failure_count"] == 0, f"Expected Axis failures = 0, got {axis_gw['recent_failure_count']}"
    print("[OK] Test G Passed: SBI failure associated exclusively with SBI Card Gateway, Axis Wallet unaffected.")

    # ----------------------------------------------------
    # TEST I: Captured payment exclusion from Amount at Risk
    # ----------------------------------------------------
    print("\n[Test I] Captured payment exclusion from Amount at Risk...")
    clear_db()
    db = SessionLocal()
    try:
        # 1 captured (INR 5000) + 1 failed (INR 1000) on Razorpay Gateway
        db.add(LivePaymentModel(
            payment_id="pay_test_i_captured", order_id="order_test_i_captured", merchant_id="m_1004",
            amount=5000.0, currency="INR", status="captured", bank="Razorpay Gateway"
        ))
        db.add(LivePaymentModel(
            payment_id="pay_test_i_failed", order_id="order_test_i_failed", merchant_id="m_1004",
            amount=1000.0, currency="INR", status="failed", bank="Razorpay Gateway"
        ))
        db.commit()
    finally:
        db.close()

    health_data = internal_service.get_gateway_health()
    rzp_gw = next((g for g in health_data if g["gateway"] == "Razorpay Gateway"), None)
    assert rzp_gw["total_transactions"] == 2, f"Expected 2 total txns, got {rzp_gw['total_transactions']}"
    assert rzp_gw["successful_transactions"] == 1, f"Expected 1 successful txn, got {rzp_gw['successful_transactions']}"
    assert rzp_gw["failed_transactions"] == 1, f"Expected 1 failed txn, got {rzp_gw['failed_transactions']}"
    assert rzp_gw["average_success_rate"] == 50.0, f"Expected 50.0% success rate, got {rzp_gw['average_success_rate']}%"
    assert rzp_gw["amount_at_risk"] == 1000.0, f"Expected INR 1000.0 at risk, got INR {rzp_gw['amount_at_risk']}"
    print("[OK] Test I Passed: Captured payment (INR 5,000) correctly excluded from amount at risk (INR 1,000).")

    # ----------------------------------------------------
    # TEST J: Multiple failed payment amount accumulation
    # ----------------------------------------------------
    print("\n[Test J] Multiple failed payment amount accumulation...")
    clear_db()
    db = SessionLocal()
    try:
        # Payment 1: INR 1000 failed, Payment 2: INR 1234 failed on HDFC Bank
        db.add(LivePaymentModel(
            payment_id="pay_test_j1", order_id="order_test_j1", merchant_id="m_1004",
            amount=1000.0, currency="INR", status="failed", bank="HDFC Bank"
        ))
        db.add(LivePaymentModel(
            payment_id="pay_test_j2", order_id="order_test_j2", merchant_id="m_1004",
            amount=1234.0, currency="INR", status="failed", bank="HDFC Bank"
        ))
        db.commit()
    finally:
        db.close()

    health_data = internal_service.get_gateway_health()
    hdfc_gw = next((g for g in health_data if g["gateway"] == "HDFC Gateway"), None)
    assert hdfc_gw["amount_at_risk"] == 2234.0, f"Expected INR 2234.0 at risk, got INR {hdfc_gw['amount_at_risk']}"
    print("[OK] Test J Passed: Multiple failed payments (INR 1,000 + INR 1,234) aggregated to exact INR 2,234.00.")

    # Reset DB to clean state after test suite execution
    clear_db()
    print("=" * 70)
    print("ALL DYNAMIC GATEWAY HEALTH QA TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_dynamic_gateway_health_suite()
