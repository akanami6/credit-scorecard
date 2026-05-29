"""
Credit Scorecard — Streamlit Cloud Deployable Version
======================================================
Standalone app with embedded scoring engine (no FastAPI dependency).
Deploy to Streamlit Cloud: https://share.streamlit.io/

Entry point: streamlit run app_cloud.py
"""
import streamlit as st
import numpy as np
import joblib
import os
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta

st.set_page_config(
    page_title="Credit Scorecard — Live Demo",
    page_icon="",
    layout="wide",
)

# ============================================================================
# Embedded scoring engine (same logic as api/scorer.py)
# ============================================================================
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'artifacts')

FEATURE_KEYS = ['fico_score', 'inq_6m', 'dti', 'revol_util', 'delinq_2yrs', 'credit_age', 'annual_inc']


@st.cache_resource
def load_artifacts():
    """Load model artifacts (cached)"""
    artifacts = {}
    artifacts['bin_boundaries'] = joblib.load(os.path.join(ARTIFACTS_DIR, 'bin_boundaries.joblib'))
    artifacts['woe_maps'] = joblib.load(os.path.join(ARTIFACTS_DIR, 'woe_maps.joblib'))
    artifacts['lr_model'] = joblib.load(os.path.join(ARTIFACTS_DIR, 'lr_model.joblib'))
    artifacts['params'] = joblib.load(os.path.join(ARTIFACTS_DIR, 'scorecard_params.joblib'))
    artifacts['risk_grades'] = joblib.load(os.path.join(ARTIFACTS_DIR, 'risk_grades.joblib'))

    import json
    with open(os.path.join(ARTIFACTS_DIR, 'model_metrics.json'), 'r') as f:
        artifacts['metrics'] = json.load(f)
    with open(os.path.join(ARTIFACTS_DIR, 'scorecard_table.json'), 'r') as f:
        artifacts['scorecard_table'] = json.load(f)

    return artifacts


def raw_to_bin(value, boundaries):
    if boundaries is None or len(boundaries) < 2:
        return 'Bin_0'
    if np.isnan(value):
        return 'Missing'
    internal_edges = boundaries[1:-1]
    if len(internal_edges) == 0:
        return 'Bin_0'
    bin_idx = int(np.digitize(value, internal_edges))
    return f'Bin_{bin_idx}'


def score_applicant(features, art):
    factor = art['params']['factor']
    intercept = art['params']['intercept']
    coefficients = art['params']['coefficients']
    base_points = art['params']['base_points']

    total_score = base_points
    feature_points = {}

    for feat in FEATURE_KEYS:
        raw_val = features.get(feat)
        if raw_val is None:
            woe_val = 0.0
        else:
            boundaries = art['bin_boundaries'].get(feat)
            woe_map = art['woe_maps'].get(feat, {})
            bin_label = raw_to_bin(raw_val, boundaries)
            woe_val = woe_map.get(bin_label, 0.0)

        woe_feat_name = feat + '_woe'
        coef = coefficients.get(woe_feat_name, 0)
        pts = -factor * coef * woe_val
        feature_points[feat] = round(float(pts), 2)
        total_score += pts

    score = int(round(np.clip(total_score, 300, 850)))

    grade = 'E'
    grade_desc = 'High Risk'
    expected_dr = 0.30
    for g, (lo, hi, desc, dr) in art['risk_grades'].items():
        if lo <= score < hi or (g == 'A' and score >= hi):
            grade = g
            grade_desc = desc
            expected_dr = dr
            break

    tz = timezone(timedelta(hours=8))
    return {
        'score': score,
        'grade': grade,
        'grade_description': grade_desc,
        'expected_default_rate': round(expected_dr, 4),
        'points_breakdown': {
            'base_points': round(base_points, 2),
            'features': feature_points,
            'total': round(float(total_score), 2),
        },
        'model_version': art['params'].get('model_version', 'v1.0'),
        'timestamp': datetime.now(tz).strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    }


# ============================================================================
# Load artifacts at startup
# ============================================================================
try:
    art = load_artifacts()
    model_ready = True
except Exception as e:
    model_ready = False
    load_error = str(e)


# ============================================================================
# UI
# ============================================================================
st.sidebar.title("Credit Scorecard")
st.sidebar.markdown("*Live Demo — Streamlit Cloud*")

if not model_ready:
    st.error(f"Failed to load model artifacts: {load_error}")
    st.stop()

# Navigation
page = st.sidebar.radio("Navigation", ["Scoring Demo", "Model Info", "About"])

# Sidebar status
st.sidebar.markdown("---")
st.sidebar.success(f"Model v{art['params'].get('model_version','?')} | AUC {art['metrics'].get('test_auc',0):.3f}")
st.sidebar.markdown("---")
st.sidebar.markdown("[GitHub Repository](https://github.com)")
st.sidebar.caption("Built with Python • scikit-learn • Streamlit")

# ============================================================================
# Page 1: Scoring Demo
# ============================================================================
if page == "Scoring Demo":
    st.title("Credit Scoring — Live Demo")
    st.markdown("Adjust the sliders to see how each factor affects the credit score in real time.")

    col_input, col_result = st.columns([1, 1.2])

    with col_input:
        st.markdown("### Applicant Profile")
        fico = st.slider("FICO Score", 300, 850, 680, 10, key="fico")
        inq_6m = st.slider("Inquiries (6 months)", 0, 15, 1, key="inq")
        dti = st.slider("DTI Ratio (%)", 0.0, 60.0, 15.0, 0.5, key="dti")
        revol_util = st.slider("Revolving Utilization (%)", 0.0, 150.0, 40.0, 1.0, key="revol")
        delinq_2yrs = st.slider("Delinquencies (2 years)", 0, 15, 0, key="delinq")
        credit_age = st.slider("Credit History (years)", 0.0, 50.0, 7.0, 0.5, key="age")
        annual_inc = st.slider("Annual Income ($)", 5000, 300000, 60000, 5000, key="inc")

        features = {
            'fico_score': fico, 'inq_6m': inq_6m, 'dti': dti,
            'revol_util': revol_util, 'delinq_2yrs': delinq_2yrs,
            'credit_age': credit_age, 'annual_inc': annual_inc,
        }

    with col_result:
        result = score_applicant(features, art)
        score = result['score']
        grade = result['grade']
        grade_colors = {'A': '#27ae60', 'B': '#2ecc71', 'C': '#f39c12', 'D': '#e67e22', 'E': '#e74c3c'}
        color = grade_colors.get(grade, '#95a5a6')

        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            delta={'reference': 600, 'increasing': {'color': 'green'}},
            number={'font': {'size': 42, 'color': color}},
            title={'text': f"Credit Score — Grade {grade}", 'font': {'size': 20}},
            gauge={
                'axis': {'range': [300, 850], 'tickwidth': 1},
                'bar': {'color': color, 'thickness': 0.25},
                'steps': [
                    {'range': [300, 560], 'color': '#fadbd8'},
                    {'range': [560, 600], 'color': '#fdebd0'},
                    {'range': [600, 640], 'color': '#fef9e7'},
                    {'range': [640, 680], 'color': '#d5f5e3'},
                    {'range': [680, 850], 'color': '#d4efdf'},
                ],
            }
        ))
        fig.update_layout(height=320, margin=dict(l=30, r=30, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # Grade info
        st.markdown(f"### Risk Grade: **{grade}** — {result['grade_description']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Score", str(score))
        c2.metric("Expected Default Rate", f"{result['expected_default_rate']:.1%}")
        c3.metric("Base Points", f"{result['points_breakdown']['base_points']:.0f}")

    # Points breakdown
    st.markdown("---")
    st.markdown("### Points Breakdown by Feature")
    breakdown = result['points_breakdown']

    feat_names = [k.replace('_', ' ').title() for k in breakdown['features'].keys()]
    feat_vals = list(breakdown['features'].values())

    fig_bar = go.Figure(go.Bar(
        x=feat_vals,
        y=feat_names,
        orientation='h',
        marker_color=[color if v > 0 else '#e74c3c' for v in feat_vals],
        text=[f"{v:+.1f}" for v in feat_vals],
        textposition='outside',
    ))
    fig_bar.update_layout(
        title="Feature Contributions to Total Score",
        xaxis_title="Points",
        height=300,
        margin=dict(l=20, r=60, t=40, b=20),
    )
    fig_bar.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.caption(f"Total Score = Base Points ({breakdown['base_points']:.1f}) + Sum of Feature Points = **{breakdown['total']:.1f}**")

# ============================================================================
# Page 2: Model Info
# ============================================================================
elif page == "Model Info":
    st.title("Model Information")

    metrics = art['metrics']
    params = art['params']

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Test AUC", f"{metrics['test_auc']:.4f}")
    col2.metric("Test KS", f"{metrics['test_ks']:.4f}")
    col3.metric("Train AUC", f"{metrics['train_auc']:.4f}")
    col4.metric("Train KS", f"{metrics['train_ks']:.4f}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Scorecard Parameters")
        st.markdown(f"""
        | Parameter | Value |
        |---|---|
        | Factor (PDO/ln2) | {params['factor']:.4f} |
        | Base Score | {params['base_score']} |
        | PDO | {params['pdo']} |
        | Base Odds | {params['base_odds']} |
        | Base Points | {params['base_points']:.2f} |
        | Intercept | {params['intercept']:.6f} |
        """)

    with col2:
        st.markdown("### Feature Importance")
        scorecard_table = art['scorecard_table']
        features = scorecard_table.get('features', {})
        feat_imp = []
        for feat_name, feat_data in features.items():
            feat_imp.append({
                'feature': feat_name.replace('_', ' ').title(),
                'coefficient': abs(feat_data['coefficient']),
            })
        import pandas as pd
        df_imp = pd.DataFrame(feat_imp).sort_values('coefficient', ascending=False)
        st.dataframe(df_imp, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Risk Grades")
    grade_data = []
    for g, (lo, hi, desc, dr) in art['risk_grades'].items():
        grade_data.append({
            'Grade': g, 'Score Range': f'{lo}-{hi}',
            'Description': desc, 'Expected Default Rate': f'{dr:.0%}'
        })
    st.dataframe(pd.DataFrame(grade_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Complete Scorecard Table")
    for feat_name, feat_data in scorecard_table.get('features', {}).items():
        with st.expander(f"{feat_name.replace('_', ' ').title()} (coef={feat_data['coefficient']:.4f})"):
            bins = feat_data.get('bins', {})
            woe_dict = feat_data.get('woe_map', {})
            rows = []
            for bin_label in sorted(bins.keys()):
                rows.append({
                    'Bin': bin_label,
                    'WOE': round(woe_dict.get(bin_label, 0), 4),
                    'Points': bins[bin_label],
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ============================================================================
# Page 3: About
# ============================================================================
elif page == "About":
    st.title("About This Project")
    st.markdown("""
    ### Credit Scorecard System

    This is a production-grade credit scoring system built with industry-standard methodology:

    - **WOE (Weight of Evidence)** encoding for risk factor quantification
    - **ChiMerge** supervised binning for optimal variable discretization
    - **Logistic Regression** with scorecard transformation (PDO scaling)
    - **7 features** selected from 13 candidates via IV → Correlation → VIF screening

    ### Tech Stack

    | Layer | Technology |
    |---|---|
    | Data Pipeline | Python • pandas • SQLite (50k records) |
    | Feature Engineering | ChiMerge • WOE • IV • VIF |
    | Model | scikit-learn LogisticRegression |
    | API | FastAPI • Pydantic • Swagger |
    | Dashboard | Streamlit • Plotly |
    | Deployment | Streamlit Cloud (this demo) |

    ### How It Works

    1. Applicant data (7 features) enters the system
    2. Raw values are mapped to bins using pre-computed boundaries
    3. Bin → WOE value lookup transforms features
    4. Logistic regression computes log-odds
    5. Score transformation converts to 300-850 scale
    6. Risk grade (A-E) is assigned based on score thresholds

    ### Run Locally

    For the full experience (API + multi-page dashboard + database):

    ```bash
    git clone <repo-url>
    cd credit-scorecard
    pip install -r requirements.txt
    python src/phase4_model_building.py   # train model
    uvicorn api.main:app --port 8000      # start API
    streamlit run dashboard/app.py         # full dashboard
    ```

    Or simply double-click `run_all.bat` on Windows.

    ### Model Performance

    - **AUC**: 0.794 (test set, 80/20 split)
    - **KS**: 0.443 (excellent discrimination)
    - **Features**: 7 (FICO, inquiries, DTI, revolving util, delinquencies, credit age, income)

    ---
    *Built as a portfolio project demonstrating end-to-end ML engineering for credit risk assessment.*
    """)

st.sidebar.markdown("---")
st.sidebar.info(
    "This is a **simplified demo** deployed on Streamlit Cloud. "
    "The full version includes a FastAPI backend, multi-page dashboard "
    "with portfolio analytics, model monitoring, and SQL data explorer. "
    "See screenshots in the GitHub README."
)
