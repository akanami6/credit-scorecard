"""验证风控数据库"""
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/risk_db.sqlite')

print('=== 风控数据库验证 ===')
print()

cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'核心表: {[t[0] for t in tables]}')

for table in tables:
    count = pd.read_sql_query(f'SELECT COUNT(*) as cnt FROM {table[0]}', conn)
    print(f'  {table[0]}: {count.iloc[0,0]:,} 行')

print()
print('--- 申请表样本 (前3行) ---')
df = pd.read_sql_query('SELECT application_id, member_id, apply_date, loan_amnt, term, purpose, annual_inc, dti, fico_score, decision FROM apply_table LIMIT 3', conn)
print(df.to_string())

print()
print('--- 借据表 loan_status 分布 ---')
stats = pd.read_sql_query('''
    SELECT loan_status, COUNT(*) as cnt, ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 2) as pct
    FROM loan_table GROUP BY loan_status
''', conn)
print(stats.to_string())

print()
print('--- 还款表状态分布 ---')
stats2 = pd.read_sql_query('''
    SELECT status, COUNT(*) as cnt FROM repayment_table GROUP BY status ORDER BY cnt DESC
''', conn)
print(stats2.to_string())

conn.close()
print()
print('[OK] 数据库验证完成')
