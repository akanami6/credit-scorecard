"""Page 4: Data Explorer"""
import streamlit as st
import pandas as pd
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'risk_db.sqlite')

st.title("Data Explorer")
st.markdown("Browse raw data tables and run safe SQL queries.")

# Table browser
st.markdown("### Table Browser")

table_choice = st.selectbox(
    "Select table:",
    options=['apply_table', 'loan_table', 'repayment_table'],
    format_func=lambda x: {
        'apply_table': 'Application Table',
        'loan_table': 'Loan Table',
        'repayment_table': 'Repayment Table'
    }.get(x, x)
)

@st.cache_data(ttl=300)
def load_table(table_name, limit=200):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def get_table_stats(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [(c[1], c[2]) for c in cursor.fetchall()]
    conn.close()
    return row_count, columns

if table_choice:
    row_count, columns = get_table_stats(table_choice)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Rows", f"{row_count:,}")
    with col2:
        st.metric("Columns", len(columns))

    st.markdown("**Schema:**")
    schema_df = pd.DataFrame(columns, columns=['Column', 'Type'])
    st.dataframe(schema_df, use_container_width=True, hide_index=True)

    st.markdown(f"**Preview (first 200 rows of {row_count:,}):**")
    df = load_table(table_choice, limit=200)
    st.dataframe(df, use_container_width=True)

    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label=f"Download {table_choice} preview as CSV",
        data=csv,
        file_name=f"{table_choice}_preview.csv",
        mime="text/csv",
    )

st.markdown("---")

# SQL Query interface
st.markdown("### SQL Query Console")
st.caption("Read-only queries. SELECT statements only. Results limited to 1000 rows.")

query = st.text_area(
    "SQL Query:",
    value="SELECT * FROM apply_table LIMIT 10",
    height=100,
    key="sql_query"
)

if st.button("Run Query"):
    # Safety check: only allow SELECT
    query_stripped = query.strip().upper()
    if not query_stripped.startswith('SELECT'):
        st.error("Only SELECT queries are allowed.")
    elif any(kw in query_stripped for kw in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']):
        st.error("Write operations (DROP, DELETE, UPDATE, INSERT, ALTER, CREATE) are not allowed.")
    else:
        try:
            # Add LIMIT if not present
            if 'LIMIT' not in query_stripped:
                query = query.rstrip(';') + ' LIMIT 1000'

            conn = sqlite3.connect(DB_PATH)
            df_result = pd.read_sql_query(query, conn)
            conn.close()

            st.success(f"Query returned {len(df_result):,} rows")
            st.dataframe(df_result, use_container_width=True)

            # Export
            csv_result = df_result.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv_result,
                file_name="query_result.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Query error: {e}")

st.markdown("---")

# Summary statistics
st.markdown("### Quick Stats")

if st.button("Generate Summary Statistics"):
    with st.spinner("Computing statistics..."):
        conn = sqlite3.connect(DB_PATH)

        # Application stats
        st.markdown("#### Application Table")
        app_stats = pd.read_sql_query("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT member_id) as unique_members,
                ROUND(AVG(fico_score), 0) as avg_fico,
                ROUND(AVG(annual_inc), 0) as avg_income,
                ROUND(AVG(dti), 1) as avg_dti,
                ROUND(AVG(revol_util), 1) as avg_revol_util
            FROM apply_table
        """, conn)
        st.dataframe(app_stats, use_container_width=True, hide_index=True)

        # Loan stats
        st.markdown("#### Loan Table")
        loan_stats = pd.read_sql_query("""
            SELECT
                COUNT(*) as total_loans,
                ROUND(AVG(loan_amnt), 0) as avg_amount,
                ROUND(AVG(int_rate), 2) as avg_rate,
                ROUND(AVG(installment), 2) as avg_installment,
                loan_status, COUNT(*) as count
            FROM loan_table
            GROUP BY loan_status
            ORDER BY count DESC
        """, conn)
        st.dataframe(loan_stats, use_container_width=True, hide_index=True)

        conn.close()
