from dotenv import load_dotenv
import os

load_dotenv()
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import merchant, internal, intelligence, demo, payments, webhooks, copilot
from intelligence.intelligence_data_service import get_intelligence_data_service
from intelligence.recovery_prediction_service import get_recovery_prediction_service

from database import init_db

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

def validate_environment_config():
    """
    Validates required production environment configuration.
    Fails safely with clear configuration error if required secrets are missing in production.
    """
    current_env = os.environ.get("ENVIRONMENT", "development")
    if current_env == "production":
        required_vars = ["RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET"]
        missing = [v for v in required_vars if not os.environ.get(v)]
        if missing:
            raise RuntimeError(
                f"[CRITICAL SECURITY CONFIGURATION ERROR] Production environment is missing required variables: {', '.join(missing)}. "
                "Please configure these variables in deployment environment or .env file before starting backend."
            )

# Execute production environment validation
validate_environment_config()

# Parse allowed CORS origins
frontend_origin = os.environ.get("FRONTEND_ORIGIN", "")
allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [orig.strip() for orig in allowed_origins_str.split(",") if orig.strip()]

if frontend_origin and frontend_origin not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(frontend_origin)

if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

# Initialize persistent SQLite database
init_db()

app = FastAPI(
    title="RecoverAI Backend API",
    description="Backend API service powered by Dataset V2 for External Merchant and Internal Operations Portals.",
    version="1.0.0"
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# CORS Middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(merchant.router)
app.include_router(internal.router)
app.include_router(intelligence.router)
app.include_router(demo.router)
app.include_router(payments.router)
app.include_router(webhooks.router)
app.include_router(copilot.router)

@app.get("/")
def root():
    return {
        "status": "RecoverAI API running",
        "environment": ENVIRONMENT
    }

@app.get("/health")
def health_check():
    """
    Production system readiness and health endpoint.
    Reports API status, dataset availability, ML model availability, and Razorpay status without exposing secrets.
    """
    try:
        ids = get_intelligence_data_service()
        dataset_available = ids.get_intelligence_dataset() is not None
    except Exception:
        dataset_available = False

    try:
        rps = get_recovery_prediction_service()
        model_available = rps.get_model_metadata() is not None
    except Exception:
        model_available = False

    from services.razorpay_service import get_razorpay_service
    rzp_service = get_razorpay_service()
    razorpay_configured = rzp_service.is_enabled()

    return {
        "status": "healthy" if (dataset_available and model_available) else "degraded",
        "environment": ENVIRONMENT,
        "api_status": "online",
        "model_available": model_available,
        "datasets_available": dataset_available,
        "razorpay_configured": razorpay_configured,
        "service": "RecoverAI Production Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("main:app", host=host, port=port, reload=True)
