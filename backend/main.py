from dotenv import load_dotenv
import os

load_dotenv()
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import merchant, internal, intelligence, demo, payments, webhooks, copilot
from intelligence.intelligence_data_service import get_intelligence_data_service
from intelligence.recovery_prediction_service import get_recovery_prediction_service

from database import init_db

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
ALLOWED_ORIGINS_STR = os.environ.get("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [orig.strip() for orig in ALLOWED_ORIGINS_STR.split(",")]

# Initialize persistent SQLite database
init_db()

app = FastAPI(
    title="RecoverAI Backend API",
    description="Backend API service powered by Dataset V2 for External Merchant and Internal Operations Portals.",
    version="1.0.0"
)


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
