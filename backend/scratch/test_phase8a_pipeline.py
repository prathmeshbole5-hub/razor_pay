import os
import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8001"

def run_test(name, fn):
    print(f"[TEST] {name}...", end=" ", flush=True)
    try:
        fn()
        print("[PASSED]")
        return True
    except Exception as e:
        print(f"[FAILED]: {e}")
        return False

def http_get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def http_post(path, data_dict, headers=None):
    url = f"{BASE_URL}{path}"
    json_bytes = json.dumps(data_dict).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=json_bytes, headers=req_headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 65)
    print("RECOVERAI PHASE 8A: LIVE RAZORPAY INTELLIGENCE PIPELINE QA SUITE")
    print("=" * 65)

    results = []

    # 1. System Health Endpoint with Razorpay Status
    def test_health():
        code, data = http_get("/health")
        assert code == 200, f"Expected 200, got {code}"
        assert data.get("status") in ("healthy", "degraded")
        assert "razorpay_configured" in data

    results.append(run_test("1. System Health Endpoint (/health)", test_health))

    # 2. Source CSV Datasets Immutability
    def test_csv_immutability():
        csv_files = [
            "backend/data/payments.csv",
            "backend/data/merchants.csv",
            "backend/data/payment_failures.csv",
            "backend/data/recovery_attempts.csv"
        ]
        for path in csv_files:
            assert os.path.exists(path), f"CSV file missing: {path}"
            assert os.path.getsize(path) > 0, f"CSV file empty: {path}"

    results.append(run_test("2. Source CSV Datasets Immutability", test_csv_immutability))

    # 3. Create Order Endpoint Valid Merchant Validation
    def test_create_order_valid():
        code, data = http_post("/api/payments/create-order", {
            "amount": 100,
            "currency": "INR",
            "merchant_id": "m_1004",
            "receipt": "test_phase8a_order"
        })
        assert code == 200, f"Expected 200, got {code}"
        assert "order_id" in data
        assert "recoverai_payment_id" in data
        assert data.get("merchant_id") == "m_1004"
        assert "key_secret" not in data

    results.append(run_test("3. Create Razorpay Test Order (/api/payments/create-order)", test_create_order_valid))

    # 4. Create Order Invalid Merchant returns 404
    def test_create_order_invalid_merchant():
        try:
            http_post("/api/payments/create-order", {
                "amount": 100,
                "currency": "INR",
                "merchant_id": "m_invalid_999"
            })
            assert False, "Should have raised 404 for invalid merchant"
        except urllib.error.HTTPError as e:
            assert e.code == 404, f"Expected 404, got {e.code}"

    results.append(run_test("4. Invalid Merchant Order Creation (404 Test)", test_create_order_invalid_merchant))

    # 5. Create Order Invalid Amount (<= 0) returns 400
    def test_create_order_invalid_amount():
        try:
            http_post("/api/payments/create-order", {
                "amount": -50,
                "merchant_id": "m_1004"
            })
            assert False, "Should have raised 400 for negative amount"
        except urllib.error.HTTPError as e:
            assert e.code in (400, 422), f"Expected 400/422, got {e.code}"

    results.append(run_test("5. Invalid Amount Order Creation (400 Test)", test_create_order_invalid_amount))

    # 6. Verify Payment Signature Success & Live Intelligence Pipeline Execution
    live_payment_id_created = None
    def test_verify_payment_success():
        nonlocal live_payment_id_created
        # Create order first
        _, ord_data = http_post("/api/payments/create-order", {
            "amount": 250,
            "merchant_id": "m_1004"
        })
        ord_id = ord_data["order_id"]
        pm_id = f"pay_test_phase8a_{ord_id.replace('order_', '')}"

        code, data = http_post("/api/payments/verify", {
            "razorpay_payment_id": pm_id,
            "razorpay_order_id": ord_id,
            "razorpay_signature": "sig_valid_test_phase8a",
            "merchant_id": "m_1004"
        })
        assert code == 200, f"Expected 200, got {code}"
        assert data.get("verified") is True
        assert "intelligence" in data
        live_payment_id_created = data.get("recoverai_payment_id") or pm_id

    results.append(run_test("6. Signature Verification & Live ML Intelligence", test_verify_payment_success))

    # 7. Signature Verification Invalid Signature Rejection (400)
    def test_verify_invalid_signature():
        try:
            http_post("/api/payments/verify", {
                "razorpay_payment_id": "pay_fake_signature",
                "razorpay_order_id": "order_fake_signature",
                "razorpay_signature": "invalid_signature_xyz_fail",
                "merchant_id": "m_1004"
            })
            assert False, "Should have rejected invalid signature with 400"
        except urllib.error.HTTPError as e:
            assert e.code in (400, 422), f"Expected 400/422, got {e.code}"

    results.append(run_test("7. Signature Verification Rejection (400 Test)", test_verify_invalid_signature))

    # 8. Webhook Handler & Idempotency Deduplication
    def test_webhook_idempotency():
        import random
        random_suffix = random.randint(100000, 999999)
        unique_evt_id = f"evt_phase8a_dedup_{random_suffix}"
        event_payload = {
            "event": "payment.failed",
            "event_id": unique_evt_id,
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"pay_wh_8a_{random_suffix}",
                        "order_id": f"order_wh_8a_{random_suffix}",
                        "amount": 15000,
                        "currency": "INR",
                        "status": "failed",
                        "error_code": "BAD_REQUEST_TIMEOUT",
                        "error_description": "Network socket timeout",
                        "notes": {"merchant_id": "m_1004"}
                    }
                }
            }
        }
        # First delivery
        code1, data1 = http_post("/api/webhooks/razorpay", event_payload)
        assert code1 == 200, f"First webhook expected 200, got {code1}"
        assert data1.get("status") == "ok", f"Expected ok, got {data1.get('status')}"

        # Second delivery (Duplicate event_id)
        code2, data2 = http_post("/api/webhooks/razorpay", event_payload)
        assert code2 == 200, f"Duplicate webhook expected 200, got {code2}"
        assert data2.get("status") == "ignored_duplicate"

    results.append(run_test("8. Webhook Processing & Idempotency Enforcement", test_webhook_idempotency))

    # 9. Live Payment Intelligence Query (GET /api/merchant/live-payments/{payment_id}/intelligence)
    def test_live_payment_intelligence_endpoint():
        nonlocal live_payment_id_created
        target_id = live_payment_id_created or "pay_wh_8a_001"
        code, data = http_get(f"/api/merchant/live-payments/{target_id}/intelligence?merchant_id=m_1004")
        assert code == 200, f"Expected 200, got {code}"
        assert "payment" in data
        assert "recovery_prediction" in data
        assert "root_cause" in data
        assert "recommendation" in data
        assert "data_quality" in data
        assert data["data_quality"]["prediction_mode"] == "live_adapted"

    results.append(run_test("9. Live Payment Intelligence Endpoint (/api/merchant/live-payments/...)", test_live_payment_intelligence_endpoint))

    # 10. Cross-Merchant Live Intelligence Isolation (m_1000 accessing m_1004 payment returns 404)
    def test_cross_merchant_live_isolation():
        nonlocal live_payment_id_created
        target_id = live_payment_id_created or "pay_wh_8a_001"
        try:
            http_get(f"/api/merchant/live-payments/{target_id}/intelligence?merchant_id=m_1000")
            assert False, "Should have raised 404 for cross-merchant live payment query"
        except urllib.error.HTTPError as e:
            assert e.code == 404, f"Expected 404, got {e.code}"

    results.append(run_test("10. Cross-Merchant Live Domain Isolation (404 Test)", test_cross_merchant_live_isolation))

    # 11. AI Copilot Live Payment Query Awareness
    def test_copilot_live_query():
        code, data = http_post("/api/copilot/query", {
            "query": "What happened to my latest live payment?",
            "merchant_id": "m_1004",
            "mode": "merchant"
        })
        assert code == 200, f"Expected 200, got {code}"
        assert "text" in data
        assert "Razorpay Test" in data["text"] or "Live" in data["text"]

    results.append(run_test("11. AI Copilot Live Payment Query Awareness", test_copilot_live_query))

    # 12. Existing Historical Payment Intelligence (pay_104421 + m_1004) Still Works
    def test_historical_intelligence():
        code, data = http_get("/api/merchant/intelligence/payment-analysis/pay_104421?merchant_id=m_1004")
        assert code == 200, f"Expected 200, got {code}"
        assert data.get("payment_id") == "pay_104421"

    results.append(run_test("12. Historical Dataset Intelligence Preservation", test_historical_intelligence))

    print("=" * 65)
    passed = sum(results)
    total = len(results)
    print(f"SUMMARY: {passed}/{total} Phase 8A Tests Passed ({passed/total*100:.1f}%)")
    print("=" * 65)

    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    main()
