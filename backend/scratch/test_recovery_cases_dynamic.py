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

def test_recovery_cases_dynamic_suite():
    print("=" * 75)
    print("RECOVERAI QA SUITE: FULL DATABASE-DRIVEN RECOVERY CASES WORKSPACE")
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

    # ----------------------------------------------------
    # TEST 1-8: Failed Payment Creates Recovery Case
    # ----------------------------------------------------
    print("\n[Test 1-8] Failed payment creates recovery case with dynamic ML intelligence...")
    merchant_id = "m_1004"
    pay_id = "pay_live_cases_01"
    order_id = "order_live_cases_01"

    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id=pay_id,
            order_id=order_id,
            merchant_id=merchant_id,
            amount=1250.0,
            currency="INR",
            status="failed",
            payment_method="UPI",
            bank="SBI Card Gateway",
            error_code="BAD_REQUEST_TIMEOUT",
            error_description="UPI PSP Server Timeout"
        ))
        db.add(AIIntelligenceResultModel(
            payment_id=pay_id,
            recovery_probability=0.72,
            prediction_band="High Recovery Probability",
            confidence_score=0.91,
            prediction_mode="live_feature_adapter",
            feature_completeness=1.0,
            root_cause=json.dumps({"primary_root_cause": {"title": "SBI PSP Latency Spike", "confidence": 0.91}}),
            recommendation=json.dumps({"recommended_strategy": {"strategy": "Alternate Payment Method"}}),
            created_at=datetime.utcnow()
        ))
        db.add(InfrastructureIncidentModel(
            incident_id="inc_cases_101",
            payment_id=pay_id,
            merchant_id=merchant_id,
            gateway="SBI Card Gateway",
            payment_method="UPI",
            error_code="BAD_REQUEST_TIMEOUT",
            title="SBI Card Gateway UPI PSP Timeout Spike",
            severity="CRITICAL",
            amount_at_risk=1250.0,
            status="ACTIVE",
            source="razorpay_test_webhook",
            affected_transactions_count=1
        ))
        db.commit()
    finally:
        db.close()

    cases = ms.get_recovery_cases(merchant_id)
    assert cases is not None and len(cases) == 1, f"Expected 1 recovery case, got {len(cases) if cases else 0}"

    c1 = cases[0]
    assert c1["payment_id"] == pay_id, f"Expected payment_id {pay_id}, got {c1['payment_id']}"
    assert c1["amount"] == 1250.0, f"Expected amount 1250.0, got {c1['amount']}"
    assert c1["failure_reason"] == "UPI PSP Server Timeout", f"Expected failure_reason, got {c1['failure_reason']}"
    assert "SBI PSP Latency" in c1["root_cause"], f"Expected SBI PSP Latency root cause, got {c1['root_cause']}"
    assert c1["recovery_probability"] == 0.72, f"Expected 0.72 probability, got {c1['recovery_probability']}"
    assert c1["strategy"] == "Alternate Payment Method", f"Expected Alternate Payment Method, got {c1['strategy']}"
    assert c1["incident_id"] == "inc_cases_101", f"Expected incident_id inc_cases_101, got {c1['incident_id']}"
    print(f"[OK] Tests 1-8 Passed: Case {c1['case_id']} dynamically created for Payment #{pay_id} (INR 1,250.00).")

    # ----------------------------------------------------
    # TEST 9-11: Action Execution Updates Case without Faking Recovery
    # ----------------------------------------------------
    print("\n[Test 9-11] Executing recovery action updates case status to ACTION_EXECUTED & AWAITING_RETRY...")
    res_act = ras.execute_recovery_action(pay_id, merchant_id, "payment_link")
    assert res_act["execution_mode"] == "TEST_SIMULATION"

    cases_after_act = ms.get_recovery_cases(merchant_id)
    c1_act = cases_after_act[0]
    assert c1_act["action_status"] == "EXECUTED", f"Expected action_status EXECUTED, got {c1_act['action_status']}"
    assert c1_act["recovery_state"] == "AWAITING_RETRY", f"Expected recovery_state AWAITING_RETRY, got {c1_act['recovery_state']}"
    assert c1_act["payment_status"] == "failed", f"Expected payment_status failed, got {c1_act['payment_status']}"
    print(f"[OK] Tests 9-11 Passed: Action executed in TEST_SIMULATION mode. Case state is AWAITING_RETRY, payment remains FAILED.")

    # ----------------------------------------------------
    # TEST 12: Duplicate Action Prevention
    # ----------------------------------------------------
    print("\n[Test 12] Duplicate action execution prevention...")
    res_dup = ras.execute_recovery_action(pay_id, merchant_id, "payment_link")
    assert res_dup["already_executed"] is True
    cases_dup = ms.get_recovery_cases(merchant_id)
    assert len(cases_dup) == 1, "Duplicate action created duplicate case records!"
    print("[OK] Test 12 Passed: Re-executing action did not duplicate case records.")

    # ----------------------------------------------------
    # TEST 13-17: Payment Success Transitions Case to RECOVERED
    # ----------------------------------------------------
    print("\n[Test 13-17] Legitimate payment success transitions case to RECOVERED...")
    lps.update_live_payment(
        razorpay_order_id=order_id,
        razorpay_payment_id=pay_id,
        status="captured",
        amount_inr=1250.0
    )

    cases_final = ms.get_recovery_cases(merchant_id)
    c1_final = cases_final[0]
    assert c1_final["recovery_state"] == "RECOVERED", f"Expected RECOVERED, got {c1_final['recovery_state']}"
    assert c1_final["payment_status"] == "captured", f"Expected captured, got {c1_final['payment_status']}"
    assert c1_final["attempt_status"] == "Recovered", f"Expected Recovered, got {c1_final['attempt_status']}"
    print("[OK] Tests 13-17 Passed: Real captured payment transitioned case to RECOVERED.")

    # ----------------------------------------------------
    # TEST 18-20: Metric Consistency & Persistence
    # ----------------------------------------------------
    print("\n[Test 18-20] Dynamic metrics consistency & persistence verification...")
    dash = ms.get_dashboard(merchant_id)
    assert dash["revenue_recovered"] == 1250.0
    assert dash["active_recovery_cases"] == 0

    timeline = ras.get_payment_timeline(pay_id, merchant_id)
    evt_types = [t["event_type"] for t in timeline]
    assert "RECOVERY_ACTION_EXECUTED" in evt_types and "PAYMENT_RECOVERED" in evt_types
    print("[OK] Tests 18-20 Passed: Dashboard metrics and timeline remain 100% consistent.")

    clear_db()
    print("=" * 75)
    print("ALL 20 FULL DATABASE-DRIVEN RECOVERY CASES TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    test_recovery_cases_dynamic_suite()
