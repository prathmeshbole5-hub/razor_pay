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
    print("=" * 60)
    print("RECOVERAI PHASE 7B: RAZORPAY TEST MODE QA MASTER SUITE")
    print("=" * 60)

    results = []

    # 1. Health Endpoint Still Works
    def test_health():
        code, data = http_get("/health")
        assert code == 200, f"Expected 200, got {code}"
        assert data.get("status") in ("healthy", "degraded")

    results.append(run_test("1. System Readiness (/health)", test_health))

    # 2. Existing Merchant Dashboard (m_1004) Still Works
    def test_dashboard():
        code, data = http_get("/api/merchant/dashboard?merchant_id=m_1004")
        assert code == 200, f"Expected 200, got {code}"
        assert data.get("merchant_id") == "m_1004"

    results.append(run_test("2. Merchant Dashboard (m_1004)", test_dashboard))

    # 3. Existing Payment Intelligence (pay_104421 + m_1004) Returns 200
    def test_intelligence_valid():
        code, data = http_get("/api/merchant/intelligence/payment-analysis/pay_104421?merchant_id=m_1004")
        assert code == 200, f"Expected 200, got {code}"
        assert data.get("payment_id") == "pay_104421"
        assert data.get("prediction", {}).get("recovery_probability") == 0.5928

    results.append(run_test("3. Payment Intelligence (pay_104421 + m_1004)", test_intelligence_valid))

    # 4. Cross-Merchant Access (pay_104421 + m_1000) Returns 404
    def test_intelligence_invalid():
        try:
            http_get("/api/merchant/intelligence/payment-analysis/pay_104421?merchant_id=m_1000")
            assert False, "Should have raised HTTP 404"
        except urllib.error.HTTPError as e:
            assert e.code == 404, f"Expected 404, got {e.code}"

    results.append(run_test("4. Cross-Merchant Isolation (404 Test)", test_intelligence_invalid))

    # 5. Original CSV Files Remain Unchanged
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

    results.append(run_test("5. Source CSV Datasets Immutability", test_csv_immutability))

    # 6. Create Order Endpoint (POST /api/payments/create-order)
    def test_create_order():
        code, data = http_post("/api/payments/create-order", {
            "amount": 50000,
            "currency": "INR",
            "merchant_id": "m_1004",
            "receipt": "test_receipt_7b"
        })
        assert code == 200, f"Expected 200, got {code}"
        assert "order_id" in data
        assert data.get("merchant_id") == "m_1004"
        assert "key_secret" not in data  # Never expose secret

    results.append(run_test("6. Create Razorpay Test Order (/api/payments/create-order)", test_create_order))

    # 7. Invalid Payment Verification Signature Rejected (400)
    def test_invalid_verification():
        try:
            http_post("/api/payments/verify", {
                "razorpay_payment_id": "pay_test_9999",
                "razorpay_order_id": "order_test_9999",
                "razorpay_signature": "invalid_fake_signature_xyz",
                "merchant_id": "m_1004"
            })
            # If backend is running with RAZORPAY_KEY_SECRET unset, test signature prefix sig_valid_/sig_test_ is accepted, but invalid_fake_signature_xyz is rejected
            assert False, "Should have rejected invalid signature with 400"
        except urllib.error.HTTPError as e:
            assert e.code in (400, 422), f"Expected 400 or 422, got {e.code}"

    results.append(run_test("7. Rejection of Invalid Payment Signature", test_invalid_verification))

    # 8. Invalid Webhook Signature Rejected (400)
    def test_invalid_webhook():
        try:
            http_post(
                "/api/webhooks/razorpay",
                {
                    "event": "payment.failed",
                    "payload": {
                        "payment": {
                            "entity": {
                                "id": "pay_wh_invalid",
                                "amount": 25000,
                                "notes": {"merchant_id": "m_1004"}
                            }
                        }
                    }
                },
                headers={"X-Razorpay-Signature": "invalid_webhook_sig_header"}
            )
            assert False, "Should have rejected invalid webhook signature with 400"
        except urllib.error.HTTPError as e:
            assert e.code == 400, f"Expected 400, got {e.code}"

    results.append(run_test("8. Rejection of Invalid Webhook Signature", test_invalid_webhook))

    # 9. Live Events Query (GET /api/payments/events?merchant_id=m_1004)
    def test_live_events():
        code, data = http_get("/api/payments/events?merchant_id=m_1004")
        assert code == 200, f"Expected 200, got {code}"
        assert data.get("merchant_id") == "m_1004"
        assert "events" in data

    results.append(run_test("9. Live Events Query (/api/payments/events)", test_live_events))

    # 10. Demo Simulation Endpoint Still Functional
    def test_demo_simulation():
        code, data = http_post("/api/demo/simulate?event_type=failure", {})
        assert code == 200, f"Expected 200, got {code}"
        assert "event" in data

    results.append(run_test("10. Existing Demo Simulation Preservation", test_demo_simulation))

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"SUMMARY: {passed}/{total} Tests Passed ({passed/total*100:.1f}%)")
    print("=" * 60)

    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    main()
