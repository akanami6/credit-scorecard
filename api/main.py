"""
FastAPI application — Credit Scorecard Scoring Service

Run: uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
Docs: http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta
import json, os

from api.config import CORS_ORIGINS, DEBUG
from api.schemas import (
    ScoreRequest, ScoreResponse, BatchScoreRequest, BatchScoreResponse,
    ModelInfoResponse, HealthResponse
)
from api.scorer import (
    score_applicant, load_artifacts, get_artifacts_status,
    _params, _metrics, _risk_grades, _feature_order, _loaded
)

app = FastAPI(
    title="Credit Scorecard API",
    description="智能信用评分卡系统 — 风控模型评分服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    load_artifacts()


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check — verifies model artifacts are loaded"""
    return {
        'status': 'healthy' if _loaded else 'degraded',
        'model_loaded': _loaded,
        'artifacts_available': get_artifacts_status(),
    }


@app.post("/score", response_model=ScoreResponse, tags=["Scoring"])
async def score_single(request: ScoreRequest):
    """
    Score a single loan applicant.

    Provide 7 features (FICO score, inquiries, DTI, etc.) and receive:
    - Credit score (300-850)
    - Risk grade (A-E)
    - Points breakdown per feature
    - Expected default rate
    """
    if not _loaded:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded")

    features = request.model_dump()
    result = score_applicant(features)
    return result


@app.post("/score/batch", response_model=BatchScoreResponse, tags=["Scoring"])
async def score_batch(request: BatchScoreRequest):
    """
    Score multiple applicants (up to 100 at once).

    Each application is scored independently using the same model.
    """
    if not _loaded:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded")

    results = []
    for app_req in request.applications:
        result = score_applicant(app_req.model_dump())
        results.append(result)

    return {'results': results, 'count': len(results)}


@app.get("/model/info", response_model=ModelInfoResponse, tags=["Model"])
async def model_info():
    """
    Get model metadata: features, performance metrics, risk grade thresholds.
    Useful for dashboard initialization and model documentation.
    """
    if not _loaded:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded")

    # Format risk grades for API response
    grades_formatted = {}
    for grade, (lo, hi, desc, dr) in _risk_grades.items():
        grades_formatted[grade] = {
            'min_score': lo,
            'max_score': hi,
            'description': desc,
            'expected_default_rate': dr,
        }

    return {
        'model_version': _params.get('model_version', 'v1.0'),
        'training_date': _params.get('training_date', 'unknown'),
        'features': [f.replace('_woe', '') for f in _params.get('feature_names', [])],
        'test_auc': _metrics.get('test_auc', 0),
        'test_ks': _metrics.get('test_ks', 0),
        'base_score': _params.get('base_score', 600),
        'pdo': _params.get('pdo', 20),
        'base_odds': _params.get('base_odds', 50),
        'risk_grades': grades_formatted,
    }


@app.get("/", tags=["System"])
async def root():
    """API root — redirects to docs"""
    return {
        'service': 'Credit Scorecard API',
        'version': '1.0.0',
        'docs': '/docs',
        'health': '/health',
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
