from fastapi import APIRouter, HTTPException, Query
from services.merchant_service import MerchantService
from intelligence.intelligence_data_service import get_intelligence_data_service
from intelligence.recovery_prediction_service import get_recovery_prediction_service
from services.root_cause_service import get_root_cause_service
from services.recommendation_service import get_recommendation_service

router = APIRouter(prefix="/api/merchant", tags=["Merchant Portal"])

merchant_service = MerchantService()
intelligence_data_service = get_intelligence_data_service()
prediction_service = get_recovery_prediction_service()
root_cause_service = get_root_cause_service()
recommendation_service = get_recommendation_service()

@router.get("/dashboard")
def get_merchant_dashboard(merchant_id: str = Query(..., description="Unique merchant ID (e.g. m_1000)")):
    data = merchant_service.get_dashboard(merchant_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Merchant '{merchant_id}' not found.")
    return data

@router.get("/payments/failed")
def get_failed_payments(merchant_id: str = Query(..., description="Unique merchant ID (e.g. m_1000)")):
    data = merchant_service.get_failed_payments(merchant_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Merchant '{merchant_id}' not found.")
    return data

@router.get("/recovery-cases")
def get_recovery_cases(merchant_id: str = Query(..., description="Unique merchant ID (e.g. m_1000)")):
    data = merchant_service.get_recovery_cases(merchant_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Merchant '{merchant_id}' not found.")
    return data

@router.get("/analytics")
def get_merchant_analytics(merchant_id: str = Query(..., description="Unique merchant ID (e.g. m_1000)")):
    data = merchant_service.get_analytics(merchant_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Merchant '{merchant_id}' not found.")
    return data

# MERCHANT-SAFE INTELLIGENCE ENDPOINTS

@router.get("/intelligence/recovery-prediction/{payment_id}")
def get_merchant_recovery_prediction(
    payment_id: str,
    merchant_id: str = Query(..., description="Unique merchant ID (e.g. m_1000)")
):
    """
    Merchant-isolated prediction endpoint. Returns 404 if payment does not belong to merchant.
    """
    derived_df = intelligence_data_service.get_intelligence_dataset()
    match = derived_df[(derived_df['payment_id'] == payment_id) & (derived_df['merchant_id'] == merchant_id)]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found for merchant '{merchant_id}'.")

    row = match.iloc[0].to_dict()
    pred = prediction_service.predict_recovery_probability(row)
    return pred

@router.get("/intelligence/payment-analysis/{payment_id}")
def get_merchant_payment_analysis(
    payment_id: str,
    merchant_id: str = Query(..., description="Unique merchant ID (e.g. m_1000)")
):
    """
    Merchant-isolated unified intelligence endpoint. Returns 404 if payment does not belong to merchant.
    Strips raw internal gateway telemetry for client security.
    """
    from services.live_payment_service import get_live_payment_service
    lps = get_live_payment_service()
    live_rec = lps.get_live_payment(payment_id, merchant_id)

    if live_rec:
        if live_rec.get("intelligence"):
            return {
                "payment_id": live_rec["payment_id"],
                "merchant_id": merchant_id,
                "amount_inr": float(live_rec.get("amount_inr", 0.0)),
                "payment_method": str(live_rec.get("payment_method", "Card")),
                "created_at": str(live_rec.get("created_at", "")),
                "prediction": live_rec["intelligence"].get("prediction"),
                "root_cause": live_rec["intelligence"].get("root_cause"),
                "recommendation": live_rec["intelligence"].get("recommendation")
            }
        from intelligence.live_payment_feature_adapter import LivePaymentFeatureAdapter
        adapted, dq = LivePaymentFeatureAdapter.adapt_live_payment(live_rec)
        pred = prediction_service.predict_recovery_probability(adapted)
        rc = root_cause_service.analyze_root_cause(live_rec["payment_id"]) or {"primary_root_cause": {"title": "Live Transaction Analysis", "reason": "Analyzed"}}
        rec = recommendation_service.recommend_recovery_strategy(live_rec["payment_id"])
        return {
            "payment_id": live_rec["payment_id"],
            "merchant_id": merchant_id,
            "amount_inr": float(live_rec.get("amount_inr", 0.0)),
            "payment_method": str(live_rec.get("payment_method", "Card")),
            "created_at": str(live_rec.get("created_at", "")),
            "prediction": pred,
            "root_cause": rc,
            "recommendation": rec
        }

    derived_df = intelligence_data_service.get_intelligence_dataset()
    match = derived_df[(derived_df['payment_id'] == payment_id) & (derived_df['merchant_id'] == merchant_id)]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found for merchant '{merchant_id}'.")

    row = match.iloc[0].to_dict()


    prediction = prediction_service.predict_recovery_probability(row)
    root_cause = root_cause_service.analyze_root_cause(payment_id)
    recommendation = recommendation_service.recommend_recovery_strategy(payment_id)

    # Sanitize root cause evidence for merchant security (remove internal gateway error rates)
    sanitized_evidence = {
        "failure_category": root_cause.get("evidence", {}).get("failure_category"),
        "error_code": root_cause.get("evidence", {}).get("error_code"),
        "payment_method": root_cause.get("evidence", {}).get("payment_method"),
        "retryable": root_cause.get("evidence", {}).get("retryable")
    }

    sanitized_root_cause = {
        "payment_id": payment_id,
        "primary_root_cause": root_cause.get("primary_root_cause"),
        "contributing_factors": [
            f for f in root_cause.get("contributing_factors", [])
            if "Gateway" not in f.get("factor", "")
        ],
        "evidence": sanitized_evidence
    }

    return {
        "payment_id": payment_id,
        "merchant_id": merchant_id,
        "amount_inr": float(row.get('amount_inr', 0.0)),
        "payment_method": str(row.get('payment_method', '')),
        "created_at": str(row.get('created_at', '')),
        "prediction": prediction,
        "root_cause": sanitized_root_cause,
        "recommendation": recommendation
    }
