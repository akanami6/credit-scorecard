"""Pydantic schemas for API request/response"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ScoreRequest(BaseModel):
    """Single applicant scoring request"""
    fico_score: int = Field(..., ge=300, le=850, description="FICO credit score (300-850)")
    inq_6m: int = Field(..., ge=0, le=20, description="Credit inquiries in last 6 months")
    dti: float = Field(..., ge=0, le=60, description="Debt-to-income ratio (%)")
    revol_util: float = Field(..., ge=0, le=150, description="Revolving utilization rate (%)")
    delinq_2yrs: int = Field(..., ge=0, le=20, description="Delinquencies in last 2 years")
    credit_age: float = Field(..., ge=0, le=50, description="Credit history length (years)")
    annual_inc: float = Field(..., ge=0, description="Annual income")


class PointsBreakdown(BaseModel):
    """Per-feature point contributions"""
    base_points: float
    features: Dict[str, float]
    total: float


class ScoreResponse(BaseModel):
    """Single applicant scoring response"""
    score: int
    grade: str
    grade_description: str
    expected_default_rate: float
    probability_bad: float
    points_breakdown: PointsBreakdown
    model_version: str
    timestamp: str


class BatchScoreRequest(BaseModel):
    """Batch scoring request"""
    applications: List[ScoreRequest] = Field(..., max_items=100)


class BatchScoreResponse(BaseModel):
    """Batch scoring response"""
    results: List[ScoreResponse]
    count: int


class ModelInfoResponse(BaseModel):
    """Model metadata response"""
    model_version: str
    training_date: str
    features: List[str]
    test_auc: float
    test_ks: float
    base_score: int
    pdo: int
    base_odds: int
    risk_grades: Dict[str, Dict[str, object]]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    artifacts_available: List[str]
