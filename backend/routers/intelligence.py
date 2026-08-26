from fastapi import APIRouter, HTTPException
from intelligence.intelligence_data_service import get_intelligence_data_service
from intelligence.recovery_prediction_service import get_recovery_prediction_service
from services.root_cause_service import get_root_cause_service
from services.recommendation_service import get_recommendation_service

router = APIRouter(prefix="/api/intelligence", tags=["Ecosystem Intelligence APIs"])

intelligence_data_service = get_intelligence_data_service()
prediction_service = get_recovery_prediction_service()
root_cause_service = get_root_cause_service()
recommendation_service = get_recommendation_service()

@router.get("/recovery-prediction/{payment_id}")
def get_recovery_prediction(payment_id: str):
    derived_df = intelligence_data_service.get_intelligence_dataset()
    match = derived_df[derived_df['payment_id'] == payment_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found.")
    
    row = match.iloc[0].to_dict()
    pred = prediction_service.predict_recovery_probability(row)
    return pred

@router.get("/root-cause/{payment_id}")
def get_root_cause(payment_id: str):
    res = root_cause_service.analyze_root_cause(payment_id)
    if res is None:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found.")
    return res

@router.get("/recommendation/{payment_id}")
def get_recommendation(payment_id: str):
    res = recommendation_service.recommend_recovery_strategy(payment_id)
    if res is None:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found.")
    return res

@router.get("/payment-analysis/{payment_id}")
def get_payment_analysis(payment_id: str):
    """
    Unified Intelligence Endpoint combining payment details, ML prediction, root cause analysis,
    and recommended recovery strategies.
    """
    derived_df = intelligence_data_service.get_intelligence_dataset()
    match = derived_df[derived_df['payment_id'] == payment_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found.")

    row = match.iloc[0].to_dict()

    prediction = prediction_service.predict_recovery_probability(row)
    root_cause = root_cause_service.analyze_root_cause(payment_id)
    recommendation = recommendation_service.recommend_recovery_strategy(payment_id)

    return {
        "payment_id": payment_id,
        "merchant_id": str(row.get('merchant_id', '')),
        "amount_inr": float(row.get('amount_inr', 0.0)),
        "payment_method": str(row.get('payment_method', '')),
        "gateway": str(row.get('gateway', '')),
        "created_at": str(row.get('created_at', '')),
        "prediction": prediction,
        "root_cause": root_cause,
        "recommendation": recommendation
    }
