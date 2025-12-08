from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.analysis import AnalysisStatus


class AnalysisCreate(BaseModel):
    original_response: str
    context: Optional[str] = None
    models: List[str]  # ["gpt4", "claude", "gemini"]


class AnalysisResponse(BaseModel):
    id: int
    user_id: int
    original_response: str
    context: Optional[str]
    models_used: List[str]
    status: AnalysisStatus
    results: Optional[Dict[str, Any]]
    credits_used: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    optimism_bias_score: int
    competitors: List[Dict[str, str]]
    market_size_reality: Dict[str, str]
    feasibility_assessment: Dict[str, str]
    risk_factors: List[str]
    final_verdict: Dict[str, Any]
