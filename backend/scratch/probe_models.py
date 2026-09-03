import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path, override=True)

api_key = os.environ.get("GEMINI_API_KEY", "").strip()
print(f"Testing API key (len={len(api_key)})")

from google import genai

client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-flash-latest"
]

working_models = []

for m in models_to_test:
    try:
        res = client.models.generate_content(model=m, contents="Say hello in 3 words")
        text = res.text.strip() if res and res.text else "empty"
        print(f"SUCCESS [{m}]: {text}")
        working_models.append(m)
    except Exception as e:
        err_msg = str(e).split("\n")[0]
        print(f"FAILED  [{m}]: {err_msg[:80]}")

print("\nSummary of WORKING models:", working_models)
