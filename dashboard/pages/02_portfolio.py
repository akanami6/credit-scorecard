"""Page 2: Portfolio Dashboard"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'risk_db.sqlite')

st.title("Portfolio Risk Dashboard")
st.markdown("Portfolio-level credit risk metrics and visualizations.")

@st.cache_data(ttl=600)
def load_portfolio_data():
    """Load aggregate portfolio data from SQLite"""
    conn = sqlite3.connect(DB_PATH)

    # Portfolio summary
    summary = pd.read_sql_query("""
        SELECT
            COUNT(DISTINCT a.application_id) as total_applications,
            SUM(CASE WHEN a.decision = 'Approved' THEN 1 ELSE 0 END) as approved,
            ROUND(AVG(CASE WHEN a.decision = 'Approved' THEN a.fico_score END), 0) as avg_fico,
            ROUND(AVG(a.annual_inc), 0) as avg_income,
            ROUND(AVG(a.dti), 1) as avg_dti
        FROM apply_table a
    """, conn)

    # Score distribution (use FICO as proxy for score distribution)
    scores = pd.read_sql_query("""
        SELECT fico_score FROM apply_table WHERE decision = 'Approved'
    """, conn)

    # Risk grade distribution (approximate from FICO)
    def fico_to_grade(fico):
        if fico >= 720: return 'A'
        elif fico >= 680: return 'B'
        elif fico >= 640: return 'C'
        elif fico >= 600: return 'D'
        else: return 'E'

    scores['grade'] = scores['fico_score'].apply(fico_to_grade)
    grade_dist = scores['grade'].value_counts().reset_index()
    grade_dist.columns = ['grade', 'count']

    # State-level breakdown
    state_stats = pd.read_sql_query("""
        SELECT
            addr_state,
            COUNT(*) as count,
            ROUND(AVG(fico_score), 0) as avg_fico,
            ROUND(AVG(annual_inc), 0) as avg_income,
            ROUND(AVG(CASE WHEN loan_table.loan_status = 'Bad' THEN 1.0 ELSE 0.0 END) * 100, 1) as bad_rate
        FROM apply_table
        LEFT JOIN loan_table ON apply_table.application_id = loan_table.application_id
        WHERE apply_table.decision = 'Approved'
        GROUP BY addr_state
        HAVING count >= 10
        ORDER BY count DESC
    """, conn)

    # Loan purpose breakdown
    purpose_stats = pd.read_sql_query("""
        SELECT
            purpose,
            COUNT(*) as count,
            ROUND(AVG(fico_score), 0) as avg_fico,
            ROUND(AVG(loan_amnt), 0) as avg_loan
        FROM apply_table
        WHERE decision = 'Approved'
        GROUP BY purpose
        ORDER BY count DESC
    """, conn)

    conn.close()
    return summary, scores, grade_dist, state_stats, purpose_stats


try:
    summary, scores, grade_dist, state_stats, purpose_stats = load_portfolio_data()

    # KPI Row
    row = summary.iloc[0]
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Applications", f"{row['total_applications']:,}")
    with col2:
        st.metric("Approval Rate", f"{row['approved']/row['total_applications']:.1%}")
    with col3:
        st.metric("Avg FICO Score", f"{row['avg_fico']:.0f}")
    with col4:
        st.metric("Avg Income", f"${row['avg_income']:,.0f}")
    with col5:
        st.metric("Avg DTI", f"{row['avg_dti']:.1f}%")

    st.markdown("---")

    # Charts row 1
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Score Distribution")
        fig_hist = px.histogram(
            scores, x='fico_score', nbins=40,
            color_discrete_sequence=['#3498db'],
            opacity=0.7, labels={'fico_score': 'FICO Score'}
        )
        fig_hist.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        fig_hist.update_traces(marker_line_width=0.5, marker_line_color='white')
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.markdown("### Risk Grade Distribution")
        grade_order = ['A', 'B', 'C', 'D', 'E']
        grade_colors_map = {'A': '#27ae60', 'B': '#2ecc71', 'C': '#f39c12', 'D': '#e67e22', 'E': '#e74c3c'}
        grade_dist['grade'] = pd.Categorical(grade_dist['grade'], categories=grade_order, ordered=True)
        grade_dist = grade_dist.sort_values('grade')

        fig_pie = px.pie(
            grade_dist, values='count', names='grade',
            color='grade', color_discrete_map=grade_colors_map,
            hole=0.4
        )
        fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        fig_pie.update_traces(textinfo='label+percent')
        st.plotly_chart(fig_pie, use_container_width=True)

    # Charts row 2
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Geographic Distribution")
        if len(state_stats) > 0:
            fig_map = px.bar(
                state_stats.head(15), x='addr_state', y='count',
                color='avg_fico', color_continuous_scale='RdBu',
                labels={'addr_state': 'State', 'count': 'Applications'},
            )
            fig_map.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Insufficient geographic data.")

    with col2:
        st.markdown("### Loan Purpose Breakdown")
        if len(purpose_stats) > 0:
            fig_purpose = px.bar(
                purpose_stats.head(10), x='purpose', y='count',
                color='avg_fico', color_continuous_scale='Blues',
                labels={'purpose': 'Loan Purpose', 'count': 'Count'},
            )
            fig_purpose.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_purpose, use_container_width=True)
        else:
            st.info("No purpose data available.")

    # State detail table
    st.markdown("---")
    st.markdown("### State-Level Risk Detail")
    st.dataframe(
        state_stats.style.format({
            'avg_fico': '{:.0f}',
            'avg_income': '${:,.0f}',
            'bad_rate': '{:.1f}%'
        }),
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.error(f"Failed to load portfolio data: {e}")
    st.info("Make sure the SQLite database exists and the API is running.")
