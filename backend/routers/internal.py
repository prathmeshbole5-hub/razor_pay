from fastapi import APIRouter, HTTPException
from services.internal_service import InternalService
from intelligence.intelligence_data_service import get_intelligence_data_service
from services.root_cause_service import get_root_cause_service
from services.recommendation_service import get_recommendation_service

router = APIRouter(prefix="/api/internal", tags=["Internal Portal"])

internal_service = InternalService()
intelligence_data_service = get_intelligence_data_service()
root_cause_service = get_root_cause_service()
recommendation_service = get_recommendation_service()

@router.get("/dashboard")
def get_internal_dashboard():
    return internal_service.get_dashboard()

@router.get("/gateway-health")
def get_gateway_health():
    return internal_service.get_gateway_health()

@router.get("/failure-intelligence")
def get_failure_intelligence():
    return internal_service.get_failure_intelligence()

@router.get("/merchant-network")
def get_merchant_network():
    return internal_service.get_merchant_network()

@router.get("/recovery-intelligence")
def get_recovery_intelligence():
    return internal_service.get_recovery_intelligence()

# INFRASTRUCTURE INCIDENT ENDPOINTS (Razorpay Internal Telemetry)

@router.get("/incidents")
def get_infrastructure_incidents():
    """
    Retrieves all ecosystem infrastructure incidents from SQLite DB.
    Includes real test payment failures and active telemetry spikes.
    """
    from services.infrastructure_incident_service import get_infrastructure_incident_service
    return get_infrastructure_incident_service().get_all_incidents()

@router.get("/incidents/{incident_id}")
def get_infrastructure_incident_by_id(incident_id: str):
    from services.infrastructure_incident_service import get_infrastructure_incident_service
    incidents = get_infrastructure_incident_service().get_all_incidents()
    for inc in incidents:
        if inc.get("id") == incident_id or inc.get("incident_id") == incident_id:
            return inc
    raise HTTPException(status_code=404, detail=f"Infrastructure incident '{incident_id}' not found.")

@router.get("/incidents/{incident_id}/payments")
def get_infrastructure_incident_affected_payments(incident_id: str):
    """
    Retrieves all live persisted payment records contributing to an infrastructure incident.
    """
    from services.infrastructure_incident_service import get_infrastructure_incident_service
    res = get_infrastructure_incident_service().get_affected_payments(incident_id)
    if res is None or res.get("status") == "error":
        raise HTTPException(status_code=404, detail=f"Infrastructure incident '{incident_id}' not found.")
    return res

@router.post("/incidents/{incident_id}/mitigate")
def mitigate_infrastructure_incident(incident_id: str):
    """
    Simulates emergency mitigation for an infrastructure incident (TEST/DEMO MODE ONLY).
    Updates incident status to MITIGATED and records audit event in SQLite DB.
    """
    from services.infrastructure_incident_service import get_infrastructure_incident_service
    res = get_infrastructure_incident_service().mitigate_incident(incident_id)
    if not res or res.get("status") == "error":
        detail_msg = res.get("message") if res else f"Infrastructure incident '{incident_id}' not found."
        raise HTTPException(status_code=404, detail=detail_msg)
    return res

# INTERNAL OPERATIONS INTELLIGENCE ENDPOINTS

@router.get("/intelligence/overview")
def get_internal_intelligence_overview():
    """
    Ecosystem-wide AI operations overview summarizing total analyzed payments,
    high-risk recovery cases, top root causes, and recovery opportunity value.
    """
    derived_df = intelligence_data_service.get_intelligence_dataset()
    total_analyzed = len(derived_df)
    
    unrecovered_df = derived_df[derived_df['recovered'] == 0]
    unrecovered_count = len(unrecovered_df)
    total_risk_inr = float(unrecovered_df['amount_inr'].sum().round(2))

    recovered_df = derived_df[derived_df['recovered'] == 1]
    total_recovered_inr = float(recovered_df['amount_inr'].sum().round(2))

    top_failures = derived_df['failure_category'].value_counts().to_dict()

    return {
        "total_payments_analyzed": total_analyzed,
        "unrecovered_risk_cases_count": unrecovered_count,
        "total_revenue_at_risk_inr": total_risk_inr,
        "total_revenue_protected_inr": total_recovered_inr,
        "ecosystem_recovery_rate_pct": float(round((len(recovered_df) / total_analyzed) * 100, 2)),
        "failure_category_breakdown": top_failures,
        "ai_status": "ONLINE",
        "model_version": "1.0.0"
    }

@router.get("/intelligence/root-causes")
def get_internal_intelligence_root_causes():
    """
    Aggregated root cause distribution across ecosystem payment failures.
    """
    return internal_service.get_failure_intelligence()

@router.get("/intelligence/recommendations")
def get_internal_intelligence_recommendations():
    """
    Aggregated recovery strategy conversion and recommendation performance matrix.
    """
    return internal_service.get_recovery_intelligence()
