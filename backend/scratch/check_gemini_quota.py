import os
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

api_key = os.environ.get("GEMINI_API_KEY", "").strip()
model_name = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash").strip()

print(f"API Key Loaded: {bool(api_key)} (Length: {len(api_key)})")
print(f"Configured Model: {model_name}")

from google import genai
from google.genai import errors

try:
    client = genai.Client(api_key=api_key)
    res = client.models.generate_content(model=model_name, contents="ping")
    print("API Call Success! Response received:")
    print(res.text[:100] if res and res.text else "Empty response")
except errors.APIError as e:
    print(f"APIError status_code: {e.code}")
    print(f"APIError message: {e.message}")
    if hasattr(e, "response_json"):
        print(f"Response JSON: {json.dumps(e.response_json, indent=2)}")
except Exception as e:
    print(f"Other Exception: {type(e).__name__}: {str(e)}")
