import sys
import os
import json
from datetime import datetime

# Ensure backend directory is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db, SessionLocal, LivePaymentModel, RecoveryActionModel, PaymentEventModel, InfrastructureIncidentModel
from services.live_payment_service import LivePaymentService
from services.recovery_action_service import RecoveryActionService
from services.merchant_service import MerchantService

def test_recovery_lifecycle_suite():
    print("=" * 75)
    print("RECOVERAI QA SUITE: RECOVERY ACTION EXECUTION & LIFECYCLE HARDENING")
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
            db.query(InfrastructureIncidentModel).delete()
            db.query(LivePaymentModel).delete()
            db.commit()
        finally:
            db.close()

    clear_db()

    # ----------------------------------------------------
    # TEST A-G: Execute Recovery Action & Validate Metadata
    # ----------------------------------------------------
    print("\n[Test A-G] Creating failed payment & executing recovery action...")
    merchant_id = "m_1004"
    pay_id = "pay_live_test_rec_01"

    # Step 1: Create live failed payment
    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id=pay_id,
            order_id="order_live_rec_01",
            merchant_id=merchant_id,
            amount=1000.0,
            currency="INR",
            status="failed",
            payment_method="Card",
            bank="Razorpay Gateway",
            error_code="international_transaction_not_allowed",
            error_description="Card restriction"
        ))
        # Add linked infrastructure incident for incident_id verification
        db.add(InfrastructureIncidentModel(
            incident_id="inc_rec_qa_101",
            payment_id=pay_id,
            merchant_id=merchant_id,
            gateway="Razorpay Gateway",
            payment_method="Card",
            error_code="international_transaction_not_allowed",
            title="Razorpay Gateway Card Restriction Spike",
            severity="WARNING",
            confidence=0.95,
            root_cause="International Card Restriction",
            amount_at_risk=1000.0,
            recommended_mitigation="Reroute traffic",
            status="ACTIVE",
            source="razorpay_test_webhook",
            affected_transactions_count=1
        ))
        db.commit()
    finally:
        db.close()

    # Initial dashboard check before action execution
    dash_before = ms.get_dashboard(merchant_id)
    assert dash_before["revenue_at_risk"] == 1000.0
    assert dash_before["revenue_recovered"] == 0.0
    assert dash_before["recovery_rate"] == 0.0

    # Execute recovery action
    res_act = ras.execute_recovery_action(pay_id, merchant_id, "payment_link")

    # Assertions for requirements A-G
    assert res_act["action_id"].startswith("rec_"), f"Expected action_id starting with rec_, got {res_act['action_id']}"
    assert res_act["payment_id"] == pay_id, f"Expected payment_id {pay_id}, got {res_act['payment_id']}"
    assert res_act["incident_id"] == "inc_rec_qa_101", f"Expected incident_id inc_rec_qa_101, got {res_act['incident_id']}"
    assert res_act["strategy"] == "Alternate Payment Method", f"Expected Alternate Payment Method, got {res_act['strategy']}"
    assert res_act["execution_status"] == "EXECUTED", f"Expected EXECUTED, got {res_act['execution_status']}"
    assert res_act["execution_mode"] == "TEST_SIMULATION", f"Expected TEST_SIMULATION, got {res_act['execution_mode']}"
    assert res_act["recovery_status"] == "AWAITING_RETRY", f"Expected AWAITING_RETRY, got {res_act['recovery_status']}"
    assert res_act["payment_status"] == "failed", f"Expected payment_status failed, got {res_act['payment_status']}"

    print(f"[OK] Tests A-G Passed: Recovery action {res_act['action_id']} executed in TEST_SIMULATION mode. Payment remains FAILED / AWAITING_RETRY.")

    # ----------------------------------------------------
    # TEST H-J: Safety Rules — Dashboard Metrics Untouched
    # ----------------------------------------------------
    print("\n[Test H-J] Verifying Safety Rule: Action execution does NOT falsely inflate Revenue Recovered...")
    dash_after_action = ms.get_dashboard(merchant_id)
    assert dash_after_action["revenue_at_risk"] == 1000.0, f"Expected 1000.0 at risk, got {dash_after_action['revenue_at_risk']}"
    assert dash_after_action["revenue_recovered"] == 0.0, f"Expected 0.0 recovered, got {dash_after_action['revenue_recovered']}"
    assert dash_after_action["recovery_rate"] == 0.0, f"Expected 0.0% recovery rate, got {dash_after_action['recovery_rate']}"
    print("[OK] Tests H-J Passed: Revenue Recovered remains 0.0 and Recovery Rate remains 0.0% after action execution.")

    # ----------------------------------------------------
    # TEST C & L: Duplicate Action Prevention & Persistence
    # ----------------------------------------------------
    print("\n[Test C & L] Duplicate action execution prevention & state persistence...")
    res_dup = ras.execute_recovery_action(pay_id, merchant_id, "payment_link")
    assert res_dup["already_executed"] is True, f"Expected already_executed=True, got {res_dup.get('already_executed')}"
    assert "already executed" in res_dup["message"].lower()

    db = SessionLocal()
    try:
        actions_cnt = db.query(RecoveryActionModel).filter_by(payment_id=pay_id).count()
        assert actions_cnt == 1, f"Expected exactly 1 RecoveryActionModel record in DB, got {actions_cnt}"
    finally:
        db.close()
    print("[OK] Tests C & L Passed: Duplicate action execution prevented cleanly. Exactly 1 action persisted in SQLite.")

    # ----------------------------------------------------
    # TEST K: Payment Timeline Audit Trail
    # ----------------------------------------------------
    print("\n[Test K] Payment timeline audit trail verification...")
    timeline = ras.get_payment_timeline(pay_id, merchant_id)
    evt_types = [t["event_type"] for t in timeline]
    assert "RECOVERY_ACTION_EXECUTED" in evt_types, f"Expected RECOVERY_ACTION_EXECUTED in timeline: {evt_types}"
    action_evt = next(t for t in timeline if t["event_type"] == "RECOVERY_ACTION_EXECUTED")
    assert "TEST SIMULATION MODE" in action_evt["description"]
    print(f"[OK] Test K Passed: Timeline contains RECOVERY_ACTION_EXECUTED event ('{action_evt['description']}').")

    # ----------------------------------------------------
    # TEST M: Closing the Loop on Real Payment Success
    # ----------------------------------------------------
    print("\n[Test M] Closing the recovery loop when legitimate payment success arrives...")
    # Update payment to captured status
    lps.update_live_payment(
        razorpay_order_id="order_live_rec_01",
        razorpay_payment_id="pay_live_test_rec_01",
        status="captured",
        payment_method="Card",
        bank="Razorpay Gateway",
        amount_inr=1000.0
    )

    # Check updated action state in DB
    db = SessionLocal()
    try:
        act_rec = db.query(RecoveryActionModel).filter_by(payment_id=pay_id).first()
        assert act_rec.recovery_state == "RECOVERED", f"Expected RECOVERED state, got {act_rec.recovery_state}"
        assert act_rec.status == "completed", f"Expected completed status, got {act_rec.status}"
    finally:
        db.close()

    # Check updated timeline
    timeline_after_success = ras.get_payment_timeline(pay_id, merchant_id)
    evt_types_after = [t["event_type"] for t in timeline_after_success]
    assert "PAYMENT_RECOVERED" in evt_types_after, f"Expected PAYMENT_RECOVERED in timeline: {evt_types_after}"

    # Check updated dashboard metrics
    dash_final = ms.get_dashboard(merchant_id)
    assert dash_final["revenue_recovered"] == 1000.0, f"Expected 1000.0 recovered, got {dash_final['revenue_recovered']}"
    assert dash_final["recovery_rate"] == 100.0, f"Expected 100.0% recovery rate, got {dash_final['recovery_rate']}"
    print("[OK] Test M Passed: Real payment success transitioned action to RECOVERED, logged PAYMENT_RECOVERED, and updated Revenue Recovered to INR 1,000.00.")

    clear_db()
    print("=" * 75)
    print("ALL RECOVERY ACTION & LIFECYCLE HARDENING TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    test_recovery_lifecycle_suite()
