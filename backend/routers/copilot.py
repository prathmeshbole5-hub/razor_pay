from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from services.copilot_service import get_copilot_service

router = APIRouter(prefix="/api/copilot", tags=["AI Copilot Intelligence"])

class CopilotQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language prompt/question")
    merchant_id: str = Field(default="m_1004", description="Merchant ID")
    mode: str = Field(default="merchant", description="'merchant' or 'internal'")

@router.post("/query")
def query_copilot(req: CopilotQueryRequest):
    """
    Processes natural language inquiries for failure intelligence, root cause analysis,
    revenue recovery predictions, and gateway telemetries.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty.")

    copilot = get_copilot_service()
    res = copilot.process_query(
        query=req.query,
        merchant_id=req.merchant_id,
        mode=req.mode
    )
    return res

@router.get("/prompts")
def get_prompts(mode: str = Query("merchant", description="'merchant' or 'internal'")):
    """
    Returns contextual suggested prompt shortcuts for the requested mode.
    """
    copilot = get_copilot_service()
    prompts = copilot.get_suggested_prompts(mode=mode)
    return {
        "mode": mode,
        "prompts": prompts
    }
