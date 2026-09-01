import sys
import os
import json
from datetime import datetime, timedelta

# Ensure backend directory is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db, SessionLocal, InfrastructureIncidentModel, LivePaymentModel, PaymentEventModel
from services.infrastructure_incident_service import InfrastructureIncidentService, INCIDENT_GROUPING_WINDOW_MINUTES

def test_incident_grouping_suite():
    print("=" * 70)
    print("RECOVERAI QA SUITE: INFRASTRUCTURE INCIDENT GROUPING & DEDUPLICATION")
    print("=" * 70)

    init_db()
    service = InfrastructureIncidentService()

    def clear_db():
        db = SessionLocal()
        try:
            db.query(PaymentEventModel).delete()
            db.query(InfrastructureIncidentModel).delete()
            db.query(LivePaymentModel).delete()
            db.commit()
        finally:
            db.close()

    # ----------------------------------------------------
    # TEST 1: First Failure Creates Incident
    # ----------------------------------------------------
    print("\n[Test 1/10] First failure creates incident...")
    clear_db()

    pay_a = {
        "payment_id": "pay_live_A",
        "merchant_id": "m_1004",
        "bank": "Razorpay Gateway",
        "payment_method": "Card",
        "error_code": "international_transaction_not_allowed",
        "error_description": "Card restriction",
        "amount_inr": 1000.0,
        "amount": 1000.0,
        "status": "failed"
    }

    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_live_A", order_id="order_live_A", merchant_id="m_1004", amount=1000.0,
            status="failed", payment_method="Card", bank="Razorpay Gateway",
            error_code="international_transaction_not_allowed"
        ))
        db.commit()
    finally:
        db.close()

    inc1 = service.process_payment_failure_incident(pay_a, {})
    assert inc1["affectedMerchants"] == 1, f"Expected 1 merchant, got {inc1['affectedMerchants']}"
    assert inc1["impactedTransactions"] == 1, f"Expected 1 transaction, got {inc1['impactedTransactions']}"
    assert inc1["amount_at_risk"] == 1000.0, f"Expected 1000.0 at risk, got {inc1['amount_at_risk']}"
    assert "Card Restriction" in inc1["title"], f"Expected Card Restriction title, got {inc1['title']}"
    print(f"[OK] Test 1 Passed: Incident {inc1['id']} created for Payment A (INR 1,000).")

    # ----------------------------------------------------
    # TEST 2: Second Matching Failure Groups Into Same Incident
    # ----------------------------------------------------
    print("\n[Test 2/10] Second matching failure groups into same incident...")
    pay_b = {
        "payment_id": "pay_live_B",
        "merchant_id": "m_1004",
        "bank": "Razorpay Gateway",
        "payment_method": "Card",
        "error_code": "international_transaction_not_allowed",
        "error_description": "Card restriction",
        "amount_inr": 1234.0,
        "amount": 1234.0,
        "status": "failed"
    }

    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_live_B", order_id="order_live_B", merchant_id="m_1004", amount=1234.0,
            status="failed", payment_method="Card", bank="Razorpay Gateway",
            error_code="international_transaction_not_allowed"
        ))
        db.commit()
    finally:
        db.close()

    inc2 = service.process_payment_failure_incident(pay_b, {})
    assert inc2["id"] == inc1["id"], f"Expected same incident ID {inc1['id']}, got {inc2['id']}"
    assert inc2["impactedTransactions"] == 2, f"Expected 2 transactions, got {inc2['impactedTransactions']}"
    assert inc2["amount_at_risk"] == 2234.0, f"Expected 2234.0 at risk, got {inc2['amount_at_risk']}"
    print(f"[OK] Test 2 Passed: Payment B grouped into existing incident {inc2['id']} (Accumulated Risk: INR 2,234.00).")

    # ----------------------------------------------------
    # TEST 3: Third Matching Failure Groups Into Same Incident
    # ----------------------------------------------------
    print("\n[Test 3/10] Third matching failure groups into same incident...")
    pay_c = {
        "payment_id": "pay_live_C",
        "merchant_id": "m_1001", # Different merchant!
        "bank": "Razorpay Gateway",
        "payment_method": "Card",
        "error_code": "international_transaction_not_allowed",
        "error_description": "Card restriction",
        "amount_inr": 500.0,
        "amount": 500.0,
        "status": "failed"
    }

    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_live_C", order_id="order_live_C", merchant_id="m_1001", amount=500.0,
            status="failed", payment_method="Card", bank="Razorpay Gateway",
            error_code="international_transaction_not_allowed"
        ))
        db.commit()
    finally:
        db.close()

    inc3 = service.process_payment_failure_incident(pay_c, {})
    assert inc3["id"] == inc1["id"], f"Expected same incident ID {inc1['id']}, got {inc3['id']}"
    assert inc3["impactedTransactions"] == 3, f"Expected 3 transactions, got {inc3['impactedTransactions']}"
    assert inc3["amount_at_risk"] == 2734.0, f"Expected 2734.0 at risk, got {inc3['amount_at_risk']}"
    assert inc3["affectedMerchants"] == 2, f"Expected 2 unique merchants, got {inc3['affectedMerchants']}"
    print(f"[OK] Test 3 Passed: Payment C grouped. 3 transactions, 2 unique merchants, INR 2,734.00 total impact.")

    # ----------------------------------------------------
    # TEST 4: Different Root Cause Creates Separate Incident
    # ----------------------------------------------------
    print("\n[Test 4/10] Different root cause creates separate incident...")
    pay_d = {
        "payment_id": "pay_live_D",
        "merchant_id": "m_1004",
        "bank": "Razorpay Gateway",
        "payment_method": "UPI",
        "error_code": "BAD_REQUEST_TIMEOUT",
        "error_description": "Timeout",
        "amount_inr": 800.0,
        "amount": 800.0,
        "status": "failed"
    }

    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_live_D", order_id="order_live_D", merchant_id="m_1004", amount=800.0,
            status="failed", payment_method="UPI", bank="Razorpay Gateway",
            error_code="BAD_REQUEST_TIMEOUT"
        ))
        db.commit()
    finally:
        db.close()

    inc4 = service.process_payment_failure_incident(pay_d, {})
    assert inc4["id"] != inc1["id"], f"Expected separate incident, but got same ID {inc1['id']}"
    assert "Timeout" in inc4["title"], f"Expected Timeout in title, got {inc4['title']}"
    assert inc4["impactedTransactions"] == 1
    assert inc4["amount_at_risk"] == 800.0
    print(f"[OK] Test 4 Passed: Payment D with Timeout error created a separate incident ({inc4['title']}).")

    # ----------------------------------------------------
    # TEST 5: Different Gateway Creates Separate Incident
    # ----------------------------------------------------
    print("\n[Test 5/10] Different gateway creates separate incident...")
    pay_e = {
        "payment_id": "pay_live_E",
        "merchant_id": "m_1004",
        "bank": "SBI Card Gateway",
        "payment_method": "UPI",
        "error_code": "BAD_REQUEST_TIMEOUT",
        "error_description": "Timeout",
        "amount_inr": 1500.0,
        "amount": 1500.0,
        "status": "failed"
    }

    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_live_E", order_id="order_live_E", merchant_id="m_1004", amount=1500.0,
            status="failed", payment_method="UPI", bank="SBI Card Gateway",
            error_code="BAD_REQUEST_TIMEOUT"
        ))
        db.commit()
    finally:
        db.close()

    inc5 = service.process_payment_failure_incident(pay_e, {})
    assert inc5["id"] != inc1["id"] and inc5["id"] != inc4["id"]
    assert inc5["gateway"] == "SBI Card Gateway"
    print(f"[OK] Test 5 Passed: SBI Card Gateway created distinct incident ({inc5['title']}).")

    # ----------------------------------------------------
    # TEST 6: Webhook Duplicate Prevention
    # ----------------------------------------------------
    print("\n[Test 6/10] Webhook duplicate prevention...")
    inc3_dup = service.process_payment_failure_incident(pay_c, {})
    assert inc3_dup["impactedTransactions"] == 3, f"Expected 3 txns after duplicate, got {inc3_dup['impactedTransactions']}"
    assert inc3_dup["amount_at_risk"] == 2734.0, f"Expected 2734.0 risk after duplicate, got {inc3_dup['amount_at_risk']}"
    print("[OK] Test 6 Passed: Re-delivering duplicate webhook for Payment C did not duplicate counts or amounts.")

    # ----------------------------------------------------
    # TEST 7: Affected Payments API Integration
    # ----------------------------------------------------
    print("\n[Test 7/10] Affected payments API get_affected_payments...")
    aff_res = service.get_affected_payments(inc1["id"])
    assert aff_res["total_transactions"] == 3, f"Expected 3 affected txns, got {aff_res['total_transactions']}"
    assert aff_res["total_amount_at_risk"] == 2734.0, f"Expected 2734.0 at risk, got {aff_res['total_amount_at_risk']}"
    pay_ids = [p["payment_id"] for p in aff_res["payments"]]
    assert "pay_live_A" in pay_ids and "pay_live_B" in pay_ids and "pay_live_C" in pay_ids
    print(f"[OK] Test 7 Passed: get_affected_payments returned all 3 persisted payment IDs {pay_ids}.")

    # ----------------------------------------------------
    # TEST 8: Time Window Expiration Creates New Incident
    # ----------------------------------------------------
    print("\n[Test 8/10] Time window expiration creates new incident...")
    db = SessionLocal()
    try:
        inc_record = db.query(InfrastructureIncidentModel).filter_by(incident_id=inc1["id"]).first()
        inc_record.updated_at = datetime.utcnow() - timedelta(minutes=INCIDENT_GROUPING_WINDOW_MINUTES + 5)
        db.commit()
    finally:
        db.close()

    pay_expired = {
        "payment_id": "pay_live_F_expired",
        "merchant_id": "m_1004",
        "bank": "Razorpay Gateway",
        "payment_method": "Card",
        "error_code": "international_transaction_not_allowed",
        "error_description": "Card restriction",
        "amount_inr": 2000.0,
        "amount": 2000.0,
        "status": "failed"
    }

    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_live_F_expired", order_id="order_live_F", merchant_id="m_1004", amount=2000.0,
            status="failed", payment_method="Card", bank="Razorpay Gateway",
            error_code="international_transaction_not_allowed"
        ))
        db.commit()
    finally:
        db.close()

    inc_expired = service.process_payment_failure_incident(pay_expired, {})
    assert inc_expired["id"] != inc1["id"], "Expected new incident after 30-minute window expiration"
    assert inc_expired["impactedTransactions"] == 1
    assert inc_expired["amount_at_risk"] == 2000.0
    print("[OK] Test 8 Passed: Failure arriving after 35 minutes created a fresh incident.")

    # ----------------------------------------------------
    # TEST 9: Mitigated Incident Handling
    # ----------------------------------------------------
    print("\n[Test 9/10] Mitigated incident handling...")
    mit_res = service.mitigate_incident(inc_expired["id"])
    assert mit_res["status"] == "mitigated"

    pay_after_mit = {
        "payment_id": "pay_live_G_after_mit",
        "merchant_id": "m_1004",
        "bank": "Razorpay Gateway",
        "payment_method": "Card",
        "error_code": "international_transaction_not_allowed",
        "error_description": "Card restriction",
        "amount_inr": 750.0,
        "amount": 750.0,
        "status": "failed"
    }

    db = SessionLocal()
    try:
        db.add(LivePaymentModel(
            payment_id="pay_live_G_after_mit", order_id="order_live_G", merchant_id="m_1004", amount=750.0,
            status="failed", payment_method="Card", bank="Razorpay Gateway",
            error_code="international_transaction_not_allowed"
        ))
        db.commit()
    finally:
        db.close()

    inc_after_mit = service.process_payment_failure_incident(pay_after_mit, {})
    assert inc_after_mit["id"] != inc_expired["id"], "Expected new active incident after previous was mitigated"
    assert inc_after_mit["status"] == "ACTIVE"
    print("[OK] Test 9 Passed: Failure after mitigation created a fresh active incident.")

    # ----------------------------------------------------
    # TEST 10: Timeline Event Integrity
    # ----------------------------------------------------
    print("\n[Test 10/10] Timeline event integrity...")
    db = SessionLocal()
    try:
        evts_a = db.query(PaymentEventModel).filter_by(payment_id="pay_live_A").all()
        evt_types = [e.event_type for e in evts_a]
        assert "INFRASTRUCTURE_INCIDENT_DETECTED" in evt_types, f"Expected INFRASTRUCTURE_INCIDENT_DETECTED in {evt_types}"
    finally:
        db.close()
    print("[OK] Test 10 Passed: Payment timeline records INFRASTRUCTURE_INCIDENT_DETECTED for affected payments.")

    clear_db()
    print("=" * 70)
    print("ALL 10 INFRASTRUCTURE INCIDENT GROUPING TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_incident_grouping_suite()
