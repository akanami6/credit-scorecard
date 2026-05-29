"""Phase 2 验证脚本 - 运行所有EDA分析"""
import sqlite3, pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import sys, warnings
warnings.filterwarnings('ignore')
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

conn = sqlite3.connect(DB_PATH)

# === 1. Roll Rate Analysis ===
print('=== 1. Roll Rate Analysis ===')
repay = pd.read_sql_query('''
    SELECT loan_id, schedule_date, dpd,
           ROW_NUMBER() OVER (PARTITION BY loan_id ORDER BY schedule_date) as period
    FROM repayment_table
''', conn)

dpd_pivot = repay.pivot(index='loan_id', columns='period', values='dpd')
print(f'Repayment matrix: {dpd_pivot.shape[0]} loans x {dpd_pivot.shape[1]} periods')

def dpd_to_stage(dpd_val):
    if pd.isna(dpd_val): return np.nan
    if dpd_val == 0: return 'M0'
    if dpd_val <= 30: return 'M1'
    if dpd_val <= 60: return 'M2'
    if dpd_val <= 90: return 'M3'
    return 'M4+'

stage_pivot = dpd_pivot.map(dpd_to_stage)

roll_rates = []
for col in range(1, min(12, stage_pivot.shape[1])):
    flow = pd.crosstab(stage_pivot[col], stage_pivot[col+1], normalize='index')
    roll_rates.append(flow)

avg_roll = sum(roll_rates) / len(roll_rates)
print('Average Roll Rate Matrix:')
print(avg_roll.round(3))
print(f'M0 stays M0: {avg_roll.loc["M0","M0"]:.1%}' if 'M0' in avg_roll.index else 'M0 data N/A')

# === 2. Vintage Analysis ===
print()
print('=== 2. Vintage Analysis ===')
loans = pd.read_sql_query('SELECT loan_id, issue_date, loan_status FROM loan_table', conn)
loans['issue_date'] = pd.to_datetime(loans['issue_date'])
loans['issue_month'] = loans['issue_date'].dt.to_period('M')

repay_detail = pd.read_sql_query('''
    SELECT r.loan_id, r.schedule_date, r.dpd, l.issue_date
    FROM repayment_table r JOIN loan_table l ON r.loan_id = l.loan_id
''', conn)
repay_detail['issue_date'] = pd.to_datetime(repay_detail['issue_date'])
repay_detail['schedule_date'] = pd.to_datetime(repay_detail['schedule_date'])
repay_detail['mob'] = (
    (repay_detail['schedule_date'].dt.year - repay_detail['issue_date'].dt.year) * 12 +
    (repay_detail['schedule_date'].dt.month - repay_detail['issue_date'].dt.month)
)
repay_detail['issue_month'] = repay_detail['issue_date'].dt.to_period('M')

vintage_data = []
for (issue_m, mob), grp in repay_detail.groupby(['issue_month', 'mob']):
    if mob < 1 or mob > 12: continue
    total_loans = grp['loan_id'].nunique()
    bad_loans = grp[grp['dpd'] >= 90]['loan_id'].nunique()
    bad_rate = bad_loans / total_loans if total_loans > 0 else 0
    vintage_data.append({'issue_month': str(issue_m), 'mob': mob, 'bad_rate': bad_rate, 'total_loans': total_loans})

vintage_df = pd.DataFrame(vintage_data)
print(f'Vintage data: {len(vintage_df)} rows')
months = sorted(vintage_df['issue_month'].unique())
print(f'Months covered: {months[0]} to {months[-1]} ({len(months)} months)')
# Show MOB12 bad rates
mob12 = vintage_df[vintage_df['mob'] == 12].sort_values('issue_month')
if len(mob12) > 0:
    print(f'MOB12 bad rate range: {mob12["bad_rate"].min():.2%} - {mob12["bad_rate"].max():.2%}')

# === 3. Univariate Analysis ===
print()
print('=== 3. Univariate Analysis ===')
df = pd.read_sql_query('''
    SELECT l.loan_id, l.loan_status, l.loan_amnt, l.term, l.int_rate, l.fico_score,
           a.annual_inc, a.dti, a.credit_age, a.revol_util,
           a.inq_6m, a.delinq_2yrs, a.pub_rec, a.purpose, a.home_ownership, a.emp_length
    FROM loan_table l JOIN apply_table a ON l.application_id = a.application_id
''', conn)
df['is_bad'] = (df['loan_status'] == 'Bad').astype(int)
print(f'Sample: {len(df):,} loans, bad rate: {df["is_bad"].mean():.2%}')

for var in ['fico_score', 'dti', 'inq_6m', 'annual_inc', 'revol_util']:
    df_temp = df[[var, 'is_bad']].dropna()
    df_temp['bin'] = pd.qcut(df_temp[var], q=5, duplicates='drop')
    stats = df_temp.groupby('bin', observed=False)['is_bad'].agg(['mean', 'count'])
    print(f'  {var:15s}: bad_rate {stats["mean"].min():.3f} -> {stats["mean"].max():.3f} (monotonic check)')

# === 4. Missing Value ===
print()
print('=== 4. Missing Value Analysis ===')
missing = df.isnull().sum()
if missing.sum() == 0:
    print('No missing values (synthetic data)')
else:
    for col in df.columns:
        if missing[col] > 0:
            print(f'  {col}: {missing[col]} missing ({missing[col]/len(df)*100:.1f}%)')

# === 5. Outlier ===
print()
print('=== 5. Outlier Analysis ===')
num_vars = ['fico_score', 'annual_inc', 'dti', 'credit_age', 'revol_util', 'inq_6m', 'delinq_2yrs', 'loan_amnt', 'int_rate']
for var in num_vars:
    q1, q3 = df[var].quantile(0.25), df[var].quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5*iqr, q3 + 1.5*iqr
    outlier_pct = ((df[var] < lower) | (df[var] > upper)).mean()
    flag = ' <-- HIGH' if outlier_pct > 0.05 else ''
    print(f'  {var:18s}: IQR={iqr:8.1f}, outlier={outlier_pct:.2%}{flag}')

# === 6. Correlation ===
print()
print('=== 6. Correlation with target ===')
corr_vars = ['fico_score', 'annual_inc', 'dti', 'credit_age', 'revol_util', 'inq_6m', 'delinq_2yrs', 'loan_amnt', 'int_rate', 'is_bad']
corr = df[corr_vars].corr()['is_bad'].drop('is_bad').sort_values(ascending=False)
for var, val in corr.items():
    bars = '+' * int(abs(val) * 50) if val > 0 else '-' * int(abs(val) * 50)
    print(f'  {var:18s}: {val:+.3f} {bars}')

conn.close()
print()
print('=' * 50)
print('[OK] Phase 2 all analyses complete!')
print('=' * 50)
