"""Page 1: Individual Applicant Scoring"""
import streamlit as st
import plotly.graph_objects as go
from dashboard.api_client import score_single, get_model_info

st.title("Credit Scoring Calculator")
st.markdown("Input applicant information to get an instant credit score and risk assessment.")

# Sidebar inputs
st.sidebar.header("Applicant Information")

fico = st.sidebar.slider("FICO Score", 300, 850, 680, 10,
    help="FICO credit score: higher is better. 680+ is considered good.")
inq_6m = st.sidebar.number_input("Inquiries (last 6 months)", 0, 20, 1,
    help="Number of credit inquiries in the past 6 months. Fewer is better.")
dti = st.sidebar.slider("DTI Ratio (%)", 0.0, 60.0, 15.0, 0.5,
    help="Debt-to-Income ratio. Lower is better. Above 43% is concerning.")
revol_util = st.sidebar.slider("Revolving Utilization (%)", 0.0, 150.0, 40.0, 1.0,
    help="Credit card balance / credit limit. Under 30% is considered good.")
delinq_2yrs = st.sidebar.number_input("Delinquencies (last 2 years)", 0, 20, 0,
    help="Number of delinquent accounts in past 2 years. 0 is ideal.")
credit_age = st.sidebar.slider("Credit History (years)", 0.0, 50.0, 7.0, 0.5,
    help="Length of credit history. Longer is better.")
annual_inc = st.sidebar.number_input("Annual Income ($)", 5000, 500000, 60000, 5000,
    help="Annual gross income. Higher income supports larger loan amounts.")

# Score button
score_btn = st.sidebar.button("Calculate Credit Score", type="primary", use_container_width=True)

# Main content area
if score_btn:
    features = {
        'fico_score': fico,
        'inq_6m': inq_6m,
        'dti': dti,
        'revol_util': revol_util,
        'delinq_2yrs': delinq_2yrs,
        'credit_age': credit_age,
        'annual_inc': annual_inc,
    }

    with st.spinner("Calculating credit score..."):
        result = score_single(features)

    if "error" in result:
        st.error(f"Scoring failed: {result['error']}")
    else:
        score = result['score']
        grade = result['grade']
        grade_desc = result['grade_description']
        prob_bad = result['probability_bad']
        expected_dr = result['expected_default_rate']
        breakdown = result['points_breakdown']

        # Grade colors
        grade_colors = {
            'A': '#27ae60', 'B': '#2ecc71', 'C': '#f39c12',
            'D': '#e67e22', 'E': '#e74c3c'
        }
        color = grade_colors.get(grade, '#95a5a6')

        # Top row: Score gauge + Grade card
        col1, col2 = st.columns([2, 1])

        with col1:
            # Plotly gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                title={'text': "Credit Score", 'font': {'size': 24}},
                number={'font': {'size': 48, 'color': color}, 'suffix': ""},
                gauge={
                    'axis': {'range': [300, 850], 'tickwidth': 1},
                    'bar': {'color': color, 'thickness': 0.3},
                    'bgcolor': 'white',
                    'borderwidth': 2,
                    'bordercolor': 'gray',
                    'steps': [
                        {'range': [300, 560], 'color': '#fadbd8'},
                        {'range': [560, 600], 'color': '#fdebd0'},
                        {'range': [600, 640], 'color': '#fef9e7'},
                        {'range': [640, 680], 'color': '#d5f5e3'},
                        {'range': [680, 850], 'color': '#d4efdf'},
                    ],
                    'threshold': {
                        'line': {'color': color, 'width': 4},
                        'thickness': 0.75,
                        'value': score
                    }
                }
            ))
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### Risk Assessment")
            st.markdown(f"## :{'green' if grade in 'AB' else 'orange' if grade == 'C' else 'red'}[{grade}] — {grade_desc}")

            metrics_data = {
                "Score": f"{score}",
                "Probability Bad": f"{prob_bad:.2%}",
                "Expected Default": f"{expected_dr:.1%}",
                "Model": result['model_version'],
            }
            for label, value in metrics_data.items():
                st.metric(label=label, value=value)

        # Points breakdown
        st.markdown("---")
        st.markdown("### Points Breakdown")

        col_a, col_b = st.columns(2)
        with col_a:
            # Bar chart of feature contributions
            feat_names = list(breakdown['features'].keys())
            feat_vals = list(breakdown['features'].values())

            fig_bar = go.Figure(go.Bar(
                x=feat_vals,
                y=[n.replace('_', ' ').title() for n in feat_names],
                orientation='h',
                marker_color=[color if v > 0 else '#e74c3c' for v in feat_vals],
                text=[f"{v:+.1f}" for v in feat_vals],
                textposition='outside',
            ))
            fig_bar.update_layout(
                title="Feature Point Contributions",
                xaxis_title="Points",
                height=350,
                margin=dict(l=20, r=40, t=40, b=20),
            )
            fig_bar.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_b:
            st.markdown("#### Score Components")
            st.metric("Base Points", f"{breakdown['base_points']:.1f}")
            for feat, pts in breakdown['features'].items():
                st.metric(f"  + {feat.replace('_', ' ').title()}", f"{pts:+.1f}")
            st.markdown("---")
            st.metric("**Total Score**", f"{breakdown['total']:.1f}")

else:
    # Default state: show model info and instructions
    st.info("Adjust the applicant parameters in the sidebar and click **Calculate Credit Score**.")

    info = get_model_info()
    if "error" not in info:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Model Information")
            st.markdown(f"- **Version**: {info.get('model_version', 'N/A')}")
            st.markdown(f"- **Training Date**: {info.get('training_date', 'N/A')}")
            st.markdown(f"- **Test AUC**: {info.get('test_auc', 0):.4f}")
            st.markdown(f"- **Test KS**: {info.get('test_ks', 0):.4f}")
        with col2:
            st.markdown("### Risk Grade Thresholds")
            grades = info.get('risk_grades', {})
            if grades:
                grade_data = []
                for g, v in sorted(grades.items()):
                    grade_data.append({
                        'Grade': g,
                        'Score Range': f"{v['min_score']}-{v['max_score']}",
                        'Description': v['description'],
                        'Default Rate': f"{v['expected_default_rate']:.0%}",
                    })
                st.dataframe(grade_data, use_container_width=True, hide_index=True)
