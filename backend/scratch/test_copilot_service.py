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
        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def http_get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def http_post(path, data_dict):
    url = f"{BASE_URL}{path}"
    json_bytes = json.dumps(data_dict).encode("utf-8")
    req = urllib.request.Request(url, data=json_bytes, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 60)
    print("RECOVERAI COPILOT QA TEST SUITE")
    print("=" * 60)

    results = []

    # 1. Test Prompts Endpoint
    def test_prompts():
        code, data = http_get("/api/copilot/prompts?mode=merchant")
        assert code == 200, f"Expected 200, got {code}"
        assert "prompts" in data
        assert len(data["prompts"]) > 0

    results.append(run_test("1. Suggested Prompts (/api/copilot/prompts)", test_prompts))

    # 2. Test Merchant Why Failures Spike Query
    def test_merchant_why_query():
        code, data = http_post("/api/copilot/query", {
            "query": "Why did my payment failures increase?",
            "merchant_id": "m_1004",
            "mode": "merchant"
        })
        assert code == 200, f"Expected 200, got {code}"
        assert "text" in data
        assert len(data.get("metrics", [])) > 0

    results.append(run_test("2. Merchant Cause Query (/api/copilot/query)", test_merchant_why_query))

    # 3. Test Specific Payment Lookup Query (pay_104421)
    def test_payment_lookup():
        code, data = http_post("/api/copilot/query", {
            "query": "Analyze pay_104421",
            "merchant_id": "m_1004",
            "mode": "merchant"
        })
        assert code == 200, f"Expected 200, got {code}"
        assert "payment_card" in data
        assert data["payment_card"]["payment_id"] == "pay_104421"

    results.append(run_test("3. Specific Payment Lookup (pay_104421)", test_payment_lookup))

    # 4. Test Internal Operations Gateway Query
    def test_internal_gateway_query():
        code, data = http_post("/api/copilot/query", {
            "query": "Which bank gateway has highest failure rate?",
            "merchant_id": "m_1004",
            "mode": "internal"
        })
        assert code == 200, f"Expected 200, got {code}"
        assert "text" in data
        assert "Internal" in data["text"] or "Gateway" in data["text"] or "Route" in data.get("metrics", [{}])[0].get("label", "")

    results.append(run_test("4. Internal Ops Gateway Query", test_internal_gateway_query))

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"SUMMARY: {passed}/{total} Copilot Tests Passed ({passed/total*100:.1f}%)")
    print("=" * 60)

    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    main()
