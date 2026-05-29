"""API client for communicating with the FastAPI scoring service"""
import requests
import streamlit as st
from typing import Dict, List, Optional

API_BASE = "http://127.0.0.1:8000"


@st.cache_data(ttl=300)
def get_health() -> dict:
    """Check API health"""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@st.cache_data(ttl=3600)
def get_model_info() -> dict:
    """Get model metadata (cached 1 hour)"""
    try:
        r = requests.get(f"{API_BASE}/model/info", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def score_single(features: dict) -> dict:
    """Score a single applicant"""
    try:
        r = requests.post(f"{API_BASE}/score", json=features, timeout=10)
        if r.status_code == 200:
            return r.json()
        return {"error": f"API returned {r.status_code}: {r.text}"}
    except Exception as e:
        return {"error": str(e)}


def score_batch(applications: List[dict]) -> dict:
    """Score multiple applicants"""
    try:
        r = requests.post(f"{API_BASE}/score/batch", json={"applications": applications}, timeout=30)
        if r.status_code == 200:
            return r.json()
        return {"error": f"API returned {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}
