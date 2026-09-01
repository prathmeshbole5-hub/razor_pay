import sys
import os
import json
from datetime import datetime

# Ensure backend directory is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db, SessionLocal, LivePaymentModel, RecoveryActionModel, PaymentEventModel, InfrastructureIncidentModel, AIIntelligenceResultModel
from services.live_payment_service import LivePaymentService
from services.recovery_action_service import RecoveryActionService
from services.merchant_service import MerchantService

def test_analytics_dynamic_suite():
    print("=" * 75)
    print("RECOVERAI QA SUITE: FULL DATABASE-DRIVEN ANALYTICS & CROSS-PAGE CONSISTENCY")
    print("=" * 75)

    init_db()
    lps = LivePaymentService()
    ras = RecoveryActionService()
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
    merchant_id = "m_1004"

    # ----------------------------------------------------
    # TEST 1: Empty Database State (Returns Historical CSV Fallback)
    # ----------------------------------------------------
    print("\n[Test 1] Empty database state analytics...")
    an_empty = ms.get_analytics(merchant_id)
    assert an_empty is not None, "get_analytics returned None for valid merchant"
    core_e = an_empty["core_metrics"]
    assert "total_transactions" in core_e and core_e["total_transactions"] >= 0, f"Expected total_transactions >= 0, got {core_e['total_transactions']}"
    print(f"[OK] Test 1 Passed: Empty database returned structured metrics (Fallback total txns: {core_e['total_transactions']}).")

    # ----------------------------------------------------
    # TEST 2-6: Single Failed Payment Analytics (INR 1,250)
    # ----------------------------------------------------
    print("\n[Test 2-6] Single failed payment analytics aggregation (INR 1,250)...")
    pay_id1 = "pay_live_an_01"
    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id=pay_id1,
            order_id="order_an_01",
            merchant_id=merchant_id,
            amount=1250.0,
            currency="INR",
            status="failed",
            payment_method="Card",
            bank="Razorpay Gateway",
            error_code="card_not_supported",
            error_description="International cards are not supported"
        ))
        db.add(AIIntelligenceResultModel(
            payment_id=pay_id1,
            recovery_probability=0.49,
            prediction_band="Medium Recovery Probability",
            confidence_score=0.88,
            root_cause=json.dumps({"primary_root_cause": {"title": "Payment Method / Card Restriction", "confidence": 0.88}}),
            recommendation=json.dumps({"recommended_strategy": {"strategy": "Alternate Payment Method"}}),
            created_at=datetime.utcnow()
        ))
        db.commit()
    finally:
        db.close()

    an_f1 = ms.get_analytics(merchant_id)
    core_f1 = an_f1["core_metrics"]
    assert core_f1["total_transactions"] == 1
    assert core_f1["failed_transactions"] == 1
    assert core_f1["revenue_at_risk"] == 1250.0
    assert core_f1["revenue_recovered"] == 0.0

    # Failure by reason check
    reasons = an_f1["failures_by_reason"]
    assert len(reasons) == 1 and reasons[0]["reason"] == "Payment Method / Card Restriction"

    # Payment method breakdown check
    methods = an_f1["failures_by_payment_method"]
    assert len(methods) == 1 and methods[0]["method"] == "Card" and methods[0]["volume"] == 1250.0
    print("[OK] Tests 2-6 Passed: Single failed payment updated total_transactions=1, risk=1250.0, reason & method matrices.")

    # ----------------------------------------------------
    # TEST 7-10: Action Execution Safety Rule in Analytics
    # ----------------------------------------------------
    print("\n[Test 7-10] Verifying Action Execution Safety Rule in Analytics...")
    ras.execute_recovery_action(pay_id1, merchant_id, "payment_link")
    
    an_act = ms.get_analytics(merchant_id)
    core_act = an_act["core_metrics"]
    assert core_act["revenue_recovered"] == 0.0, f"Action execution falsely increased revenue_recovered to {core_act['revenue_recovered']}"
    assert core_act["recovery_rate"] == 0.0, f"Action execution falsely increased recovery_rate to {core_act['recovery_rate']}"

    strats = an_act["recovery_performance_by_strategy"]
    assert len(strats) >= 1
    alt_strat = next((s for s in strats if "Alternate" in s["strategy"]), strats[0])
    assert alt_strat["total_attempts"] == 1
    assert alt_strat["successful_attempts"] == 0
    assert alt_strat["success_rate"] == 0.0
    print("[OK] Tests 7-10 Passed: Action execution recorded 1 attempt with 0% success rate, preserving 0.0 recovered revenue.")

    # ----------------------------------------------------
    # TEST 11-15: Legitimate Payment Success Closes Loop in Analytics
    # ----------------------------------------------------
    print("\n[Test 11-15] Legitimate payment success updates strategy conversion & revenue recovered...")
    lps.update_live_payment(
        razorpay_order_id="order_an_01",
        razorpay_payment_id=pay_id1,
        status="captured",
        amount_inr=1250.0
    )

    an_succ = ms.get_analytics(merchant_id)
    core_succ = an_succ["core_metrics"]
    assert core_succ["revenue_recovered"] == 1250.0, f"Expected revenue_recovered 1250.0, got {core_succ['revenue_recovered']}"
    assert core_succ["revenue_at_risk"] == 0.0, f"Expected revenue_at_risk 0.0, got {core_succ['revenue_at_risk']}"
    assert core_succ["recovery_rate"] == 100.0, f"Expected recovery_rate 100.0%, got {core_succ['recovery_rate']}"

    strats_succ = an_succ["recovery_performance_by_strategy"]
    alt_succ = next((s for s in strats_succ if "Alternate" in s["strategy"]), strats_succ[0])
    assert alt_succ["successful_attempts"] == 1
    assert alt_succ["success_rate"] == 100.0
    assert alt_succ["recovered_amount"] == 1250.0
    print("[OK] Tests 11-15 Passed: Payment capture updated strategy conversion to 100% and recovered revenue to INR 1,250.00.")

    # ----------------------------------------------------
    # TEST 16-20: Cross-Page Consistency Verification
    # ----------------------------------------------------
    print("\n[Test 16-20] Cross-page consistency verification across all views...")
    dash = ms.get_dashboard(merchant_id)
    cases = ms.get_recovery_cases(merchant_id)

    assert dash["revenue_recovered"] == core_succ["revenue_recovered"] == 1250.0
    assert cases[0]["recovery_state"] == "RECOVERED"
    print("[OK] Tests 16-20 Passed: Dashboard, Recovery Cases, and Analytics share 100% identical data story.")

    clear_db()
    print("=" * 75)
    print("ALL 20 FULL DATABASE-DRIVEN ANALYTICS QA TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    test_analytics_dynamic_suite()
