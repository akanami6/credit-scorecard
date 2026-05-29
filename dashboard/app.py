"""
Credit Scorecard Dashboard — Main Entry
Run: streamlit run dashboard/app.py --server.port 8501
"""
import streamlit as st

st.set_page_config(
    page_title="Credit Scorecard System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("Credit Scorecard")
st.sidebar.markdown("---")
st.sidebar.markdown("### 智能信用评分卡系统")
st.sidebar.markdown("基于逻辑回归的标准评分卡模型")
st.sidebar.markdown("---")
st.sidebar.info(
    "**7 Features**\n\n"
    "FICO · Inquiries · DTI · Revolving Util\n\n"
    "Delinquencies · Credit Age · Annual Income"
)
st.sidebar.markdown("---")
st.sidebar.caption("v1.0 | Phase 1-7 Complete")

# Check API connection
from dashboard.api_client import get_health

health = get_health()
if health.get("status") == "healthy":
    st.sidebar.success("API Connected")
else:
    st.sidebar.error("API Offline — start with: run_api.bat")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Pages:**\n"
    "1. Scoring — Individual applicant scoring\n"
    "2. Portfolio — Portfolio-level metrics\n"
    "3. Model Monitor — KS, PSI, WOE curves\n"
    "4. Data Explorer — SQL & table browser"
)


# === Main Page Content ===
st.title("Credit Scorecard System")
st.markdown("### 智能信用评分卡 — 风控决策引擎")

col1, col2, col3, col4 = st.columns(4)

try:
    info = get_model_info()
    if "error" not in info:
        with col1:
            st.metric("Model AUC", f"{info.get('test_auc', 0):.3f}")
        with col2:
            st.metric("Model KS", f"{info.get('test_ks', 0):.3f}")
        with col3:
            st.metric("Features", len(info.get('features', [])))
        with col4:
            st.metric("Base Score", info.get('base_score', 600))
except Exception:
    pass

st.markdown("---")

st.markdown("""
### Architecture

```
Applicant Data (7 features)
       |
       v
[FastAPI Scoring Service]  <--  Logistic Regression Scorecard
       |                         WOE Encoding + Points Transformation
       v
Credit Score (300-850) + Risk Grade (A/B/C/D/E) + Points Breakdown
       |
       v
[Streamlit Dashboard]  --  Visualization & Monitoring
```

### How to Use

1. **Start API**: Double-click `run_api.bat` (or `uvicorn api.main:app --port 8000`)
2. **Start Dashboard**: Double-click `run_dashboard.bat` (or `streamlit run dashboard/app.py`)
3. **Scoring**: Go to page 1, input applicant info, get instant credit score
4. **Portfolio**: Go to page 2 for portfolio-level risk analytics
5. **Monitor**: Go to page 3 for model performance monitoring
6. **Explore**: Go to page 4 to browse raw data

### Risk Grades

| Grade | Score Range | Description | Expected Default Rate |
|-------|------------|-------------|----------------------|
| A | 680+ | Very Low Risk | 5% |
| B | 640-680 | Low Risk | 8% |
| C | 600-640 | Medium Risk | 12% |
| D | 560-600 | Higher Risk | 18% |
| E | <560 | High Risk | 30% |

### API Endpoints (FastAPI Swagger)

- `POST /score` — Single applicant scoring
- `POST /score/batch` — Batch scoring (up to 100)
- `GET /model/info` — Model metadata & performance
- `GET /health` — Service health check
- `GET /docs` — Interactive Swagger documentation
""")
