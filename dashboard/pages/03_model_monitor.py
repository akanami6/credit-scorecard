"""Page 3: Model Monitoring"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import os
import json
import joblib

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'risk_db.sqlite')
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'artifacts')

st.title("Model Performance Monitor")
st.markdown("Track model stability and performance over time.")

@st.cache_data(ttl=600)
def load_model_artifacts():
    """Load artifacts for monitoring visualizations"""
    woe_maps = joblib.load(os.path.join(ARTIFACTS_DIR, 'woe_maps.joblib'))
    bin_boundaries = joblib.load(os.path.join(ARTIFACTS_DIR, 'bin_boundaries.joblib'))
    params = joblib.load(os.path.join(ARTIFACTS_DIR, 'scorecard_params.joblib'))

    with open(os.path.join(ARTIFACTS_DIR, 'model_metrics.json'), 'r') as f:
        metrics = json.load(f)
    with open(os.path.join(ARTIFACTS_DIR, 'scorecard_table.json'), 'r') as f:
        scorecard_table = json.load(f)

    return woe_maps, bin_boundaries, params, metrics, scorecard_table


try:
    woe_maps, bin_boundaries, params, metrics, scorecard_table = load_model_artifacts()

    # Model performance summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Test AUC", f"{metrics.get('test_auc', 0):.4f}")
    with col2:
        st.metric("Test KS", f"{metrics.get('test_ks', 0):.4f}")
    with col3:
        st.metric("Train AUC", f"{metrics.get('train_auc', 0):.4f}")
    with col4:
        st.metric("Train KS", f"{metrics.get('train_ks', 0):.4f}")

    st.markdown("---")

    # Feature importance
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Feature Importance (|Coefficient|)")

        features = scorecard_table.get('features', {})
        feat_imp = []
        for feat_name, feat_data in features.items():
            feat_imp.append({
                'feature': feat_name.replace('_', ' ').title(),
                'coefficient': abs(feat_data['coefficient']),
            })
        df_imp = pd.DataFrame(feat_imp).sort_values('coefficient')

        fig_imp = px.bar(
            df_imp, x='coefficient', y='feature', orientation='h',
            color='coefficient', color_continuous_scale='Blues',
            labels={'coefficient': '|Coefficient|', 'feature': ''},
        )
        fig_imp.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_imp, use_container_width=True)

    with col2:
        st.markdown("### Scorecard Parameters")
        st.markdown(f"""
        | Parameter | Value |
        |---|---|
        | Factor (PDO/ln2) | {params['factor']:.4f} |
        | Offset | {params['offset']:.4f} |
        | Base Points | {params['base_points']:.2f} |
        | Intercept | {params['intercept']:.6f} |
        | Base Score | {params['base_score']} |
        | PDO | {params['pdo']} |
        | Base Odds | {params['base_odds']} |
        """)

    st.markdown("---")

    # WOE Curve Viewer
    st.markdown("### WOE Curves by Feature")
    st.markdown("Shows how each feature bin contributes to risk prediction.")

    selected_feature = st.selectbox(
        "Select feature to view WOE curve:",
        options=list(woe_maps.keys()),
        format_func=lambda x: x.replace('_', ' ').title()
    )

    if selected_feature:
        woe_map = woe_maps[selected_feature]
        boundaries = bin_boundaries.get(selected_feature)

        # Sort bins and their WOE values
        sorted_bins = sorted(woe_map.items(), key=lambda x: x[0])
        bin_labels = [b[0] for b in sorted_bins]
        woe_values = [b[1] for b in sorted_bins]

        fig_woe = go.Figure()

        # Bar chart for WOE
        colors_woe = ['#2ecc71' if v > 0 else '#e74c3c' for v in woe_values]
        fig_woe.add_trace(go.Bar(
            x=bin_labels, y=woe_values,
            marker_color=colors_woe,
            text=[f"{v:.3f}" for v in woe_values],
            textposition='outside',
            name='WOE'
        ))

        # Line for trend
        fig_woe.add_trace(go.Scatter(
            x=bin_labels, y=woe_values,
            mode='lines+markers',
            line=dict(color='#2c3e50', width=2),
            marker=dict(size=8),
            name='Trend'
        ))

        fig_woe.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5,
                         annotation_text="WOE=0 (no predictive power)")

        fig_woe.update_layout(
            title=f"WOE Curve — {selected_feature.replace('_', ' ').title()}",
            xaxis_title="Bin",
            yaxis_title="WOE Value",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_woe, use_container_width=True)

        # WOE interpretation
        st.markdown("**Interpretation:**")
        st.markdown("- WOE > 0: This bin has more GOOD customers than average")
        st.markdown("- WOE < 0: This bin has more BAD customers than average")
        st.markdown("- WOE = 0: This bin does not discriminate between good and bad")
        st.markdown("- Monotonic WOE (consistently increasing or decreasing) is ideal for scorecard interpretability")

    st.markdown("---")

    # Scorecard table
    st.markdown("### Complete Scorecard Table")
    st.markdown("Points contributed by each feature bin to the final credit score.")

    base_pts = scorecard_table.get('base_points', 0)
    st.metric("Base Points (everyone starts here)", f"{base_pts:.1f}")

    for feat_name, feat_data in scorecard_table.get('features', {}).items():
        with st.expander(f"{feat_name.replace('_', ' ').title()} (coef={feat_data['coefficient']:.4f})"):
            bins = feat_data.get('bins', {})
            woe_dict = feat_data.get('woe_map', {})

            rows = []
            for bin_label in sorted(bins.keys()):
                rows.append({
                    'Bin': bin_label,
                    'WOE': woe_dict.get(bin_label, 0),
                    'Points': bins[bin_label],
                })
            df_bins = pd.DataFrame(rows)
            st.dataframe(df_bins, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Failed to load model artifacts: {e}")
