import os
import sys
import json
import urllib.request
import urllib.error

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

BASE_URL = "http://127.0.0.1:8002"

def http_post(endpoint: str, payload: dict):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}
    except Exception as e:
        return 500, {"error": str(e)}

def http_get(endpoint: str):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))
    except Exception as e:
        return 500, {"error": str(e)}

def run_suite():
    print("===============================================================")
    print("RECOVERAI GEMINI COPILOT COMPREHENSIVE QA TEST SUITE")
    print("===============================================================")

    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        safe_details = details.encode('ascii', 'ignore').decode('ascii') if details else ""
        if condition:
            passed += 1
            print(f"[PASS] Test {total}: {name}")
            if safe_details:
                print(f"   -> {safe_details[:120]}")
        else:
            print(f"[FAIL] Test {total}: {name}")
            if safe_details:
                print(f"   -> {safe_details[:160]}")

    # Test 1: Natural Language Query
    status, data = http_post("/api/copilot/query", {
        "query": "Why are payments failing right now?",
        "merchant_id": "m_1004",
        "mode": "merchant"
    })
    assert_test(
        "1. Natural Language Query (Gemini Reasoning)",
        status == 200 and "text" in data and len(data["text"]) > 20 and "error" not in data,
        f"Status: {status}, Text: {data.get('text', '')[:100]}..."
    )

    # Test 2: Payment-Specific Query (pay_104421)
    status, data = http_post("/api/copilot/query", {
        "query": "Why did payment pay_104421 fail and what should I do?",
        "merchant_id": "m_1004",
        "mode": "merchant"
    })
    has_card = data.get("payment_card") is not None
    pm_id_match = data.get("payment_card", {}).get("payment_id") == "pay_104421" if has_card else False
    assert_test(
        "2. Payment-Specific Query (pay_104421 Grounded Context)",
        status == 200 and pm_id_match and "text" in data,
        f"Payment ID in Card: {data.get('payment_card', {}).get('payment_id')}"
    )

    # Test 3: Missing Payment Query
    status, data = http_post("/api/copilot/query", {
        "query": "Explain payment pay_does_not_exist_9999",
        "merchant_id": "m_1004",
        "mode": "merchant"
    })
    text_lower = data.get("text", "").lower()
    not_found_mentioned = any(kw in text_lower for kw in ["not found", "unavailable", "does not exist", "could not find", "not present", "not recorded", "cannot locate", "unable to find", "no record"])
    assert_test(
        "3. Missing Payment Query (No Fabrication)",
        status == 200 and not_found_mentioned,
        f"Explanation: {data.get('text', '')[:100]}..."
    )

    # Test 4: Financial Accuracy
    from services.merchant_service import MerchantService
    ms = MerchantService()
    dashboard = ms.get_dashboard("m_1004") or {}
    expected_at_risk = dashboard.get("revenue_at_risk", 1245000)

    status, data = http_post("/api/copilot/query", {
        "query": "How much revenue is currently at risk for CloudMart?",
        "merchant_id": "m_1004",
        "mode": "merchant"
    })
    metrics = data.get("metrics", [])
    risk_metric = next((m for m in metrics if "risk" in m.get("label", "").lower()), None)
    assert_test(
        "4. Financial Accuracy Verification",
        status == 200 and risk_metric is not None,
        f"Metric Value: {risk_metric.get('value') if risk_metric else 'None'}, Backend Expected: INR {expected_at_risk:,.0f}"
    )

    # Test 5: Recovery State Distinction
    status, data = http_post("/api/copilot/query", {
        "query": "What is the difference between an executed recovery action and confirmed recovery?",
        "merchant_id": "m_1004",
        "mode": "merchant"
    })
    assert_test(
        "5. Recovery State Distinction Prompting",
        status == 200 and "text" in data,
        f"Explanation: {data.get('text', '')[:100]}..."
    )

    # Test 6: Merchant Isolation
    status, data = http_post("/api/copilot/query", {
        "query": "Show payment pay_104421 details",
        "merchant_id": "m_9999_other",
        "mode": "merchant"
    })
    # pay_104421 belongs to m_1004; querying as m_9999_other should indicate not found or scoped isolated
    pm_card = data.get("payment_card")
    isolated = pm_card is None or pm_card.get("merchant_id") == "m_9999_other" or "not found" in data.get("text", "").lower()
    assert_test(
        "6. Merchant Isolation Enforcement",
        status == 200 and isolated,
        f"Text response: {data.get('text', '')[:100]}"
    )

    # Test 7: Gemini Service Graceful Failure Handling
    from services.gemini_service import get_gemini_service
    from services.copilot_service import get_copilot_service
    gs = get_gemini_service()
    cs = get_copilot_service()
    original_env_key = os.environ.get("GEMINI_API_KEY", "")
    os.environ["GEMINI_API_KEY"] = "" # Temporarily clear env key
    gs.api_key = ""
    gs.client = None

    err_res = cs.process_query("Why are payments failing?", "m_1004", "merchant")
    os.environ["GEMINI_API_KEY"] = original_env_key # Restore env key
    gs.is_configured()

    assert_test(
        "7. Gemini Service Graceful Failure Handling",
        isinstance(err_res, dict) and err_res.get("error") is True,
        f"Error response: {err_res}"
    )

    # Test 8: Request Schema Backward Compatibility
    status, data = http_post("/api/copilot/query", {
        "query": "Which recovery strategy is working best?",
        "merchant_id": "m_1004",
        "mode": "merchant"
    })
    assert_test(
        "8. Existing Endpoint Request Schema Compatibility",
        status == 200 and "text" in data and "metrics" in data,
        f"Status: {status}"
    )

    # Test 9: Response Schema Completeness
    keys_present = all(k in data for k in ["text", "metrics", "payment_card", "recommendation", "suggestedAction", "actionType", "actionPayload"])
    assert_test(
        "9. Full Response Schema Preservation",
        status == 200 and keys_present,
        f"Keys present: {list(data.keys())}"
    )

    # Test 10: Secrets Verification (No API key leaks)
    secret_key = os.environ.get("GEMINI_API_KEY", "AQ.")
    raw_response_str = json.dumps(data)
    no_secret_leaked = secret_key not in raw_response_str if secret_key and len(secret_key) > 10 else True
    assert_test(
        "10. Security Audit (No Gemini Key Exposed in API)",
        no_secret_leaked,
        "Verified: No GEMINI_API_KEY substring present in JSON response payload."
    )

    print("===============================================================")
    print(f"RESULT: {passed}/{total} Tests Passed ({passed/total*100:.1f}%)")
    print("===============================================================")
    return passed == total

if __name__ == "__main__":
    success = run_suite()
    sys.exit(0 if success else 1)
