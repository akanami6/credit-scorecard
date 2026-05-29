"""
数据加载模块
模拟真实风控数仓的数据提取流程

在真实公司里:
- 风控分析师不直接访问生产数据库
- 通过数据仓库(数仓)团队的接口取数
- 取数流程: 提需求 -> 数仓写SQL -> 导出CSV/表 -> 分析师用
- 这里用 Python + SQLite 模拟这个过程
"""
import pandas as pd
import numpy as np
import sqlite3
import os
import zipfile
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_RAW, DB_PATH, DATABASE_URL


def download_lending_club_data():
    """
    下载Lending Club数据集
    数据来源: Lending Club 公开发布的借贷数据(已停更)
    这里下载 2018-2019 年的数据用于项目
    """
    import urllib.request

    # Lending Club历史数据镜像 (2018 Q1-Q4)
    # 这些是公开的学术镜像源
    files = {
        "2018": "https://resources.lendingclub.com/LoanStats_2018Q4.csv.zip",
        # 如果主源失败，尝试备用源
        "2018_alt": "https://github.com/nickkuo/LendingClub/raw/master/LoanStats_2018Q4.csv.zip",
    }

    os.makedirs(DATA_RAW, exist_ok=True)
    target = os.path.join(DATA_RAW, "LoanStats_2018Q4.csv")

    # 如果数据已经存在，直接返回
    if os.path.exists(target):
        print(f"[INFO] 数据已存在: {target}")
        return target

    print("[INFO] 正在下载 Lending Club 2018Q4 数据...")
    print("[INFO] 真实场景: 这一步相当于向数仓团队申请数据导出")

    for name, url in files.items():
        try:
            zip_path = os.path.join(DATA_RAW, "LoanStats_2018Q4.csv.zip")
            print(f"  尝试: {name} -> {url[:60]}...")
            urllib.request.urlretrieve(url, zip_path)

            # 解压
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(DATA_RAW)
            os.remove(zip_path)
            print(f"[OK] 数据下载并解压成功: {target}")
            return target
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            continue

    print("[WARN] 无法下载真实数据，将使用合成数据")
    return None


def generate_synthetic_data(n_samples=50000):
    """
    生成合成风控数据
    如果无法下载真实数据，用这个生成结构相同的模拟数据
    数据的变量定义和分布参照真实Lending Club数据

    重要: 这并不是'假'数据，在实际工作中，当你入职一家新公司
    拿不到生产数据时，用合成数据验证方法论是完全合理的
    """
    print(f"[INFO] 生成 {n_samples} 条合成借贷数据")
    print("[INFO] 变量结构和分布参照真实Lending Club数据")

    np.random.seed(42)

    # 借款金额 (真实范围: 1000-40000)
    loan_amnt = np.random.lognormal(mean=8.5, sigma=0.8, size=n_samples)
    loan_amnt = np.clip(loan_amnt, 1000, 40000).astype(int)

    # 年收入 (真实范围: 12000-500000)
    annual_inc = np.random.lognormal(mean=10.8, sigma=0.6, size=n_samples)
    annual_inc = np.clip(annual_inc, 12000, 500000).astype(int)

    # DTI (Debt-to-Income ratio, 负债收入比, 0-40%)
    dti = np.random.beta(a=2, b=5, size=n_samples) * 40
    dti = np.round(dti, 2)

    # 借款期限 (36或60个月)
    term = np.random.choice([36, 60], size=n_samples, p=[0.7, 0.3])

    # FICO分数范围 (真实: 660-850)
    fico = np.random.normal(loc=700, scale=35, size=n_samples)
    fico = np.clip(fico, 580, 850).astype(int)

    # 信用历史长度 (年)
    credit_age_years = np.random.beta(a=2, b=3, size=n_samples) * 30
    credit_age_years = np.round(credit_age_years, 1)

    # 循环额度利用率 (0-100%)
    revol_util = np.random.beta(a=3, b=5, size=n_samples) * 100
    revol_util = np.round(revol_util, 1)

    # 最近6个月查询次数
    inquiries_6m = np.random.poisson(lam=1.5, size=n_samples)
    inquiries_6m = np.clip(inquiries_6m, 0, 10)

    # 逾期次数 (最近2年)
    delinq_2yrs = np.random.poisson(lam=0.5, size=n_samples)
    delinq_2yrs = np.clip(delinq_2yrs, 0, 10)

    # 违约记录数
    pub_rec = np.random.poisson(lam=0.1, size=n_samples)
    pub_rec = np.clip(pub_rec, 0, 5)

    # 借款目的
    purpose = np.random.choice(
        ['debt_consolidation', 'credit_card', 'home_improvement',
         'major_purchase', 'small_business', 'car', 'medical',
         'moving', 'vacation', 'other'],
        size=n_samples,
        p=[0.40, 0.20, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03, 0.02, 0.02]
    )

    # 房屋拥有状态
    home_ownership = np.random.choice(
        ['MORTGAGE', 'RENT', 'OWN'],
        size=n_samples,
        p=[0.50, 0.40, 0.10]
    )

    # 工作年限
    emp_length = np.random.choice(
        ['< 1 year', '1 year', '2 years', '3 years', '4 years',
         '5 years', '6 years', '7 years', '8 years', '9 years', '10+ years'],
        size=n_samples,
        p=[0.05, 0.08, 0.10, 0.10, 0.09, 0.10, 0.09, 0.09, 0.08, 0.07, 0.15]
    )

    # 地区 (简化)
    addr_state = np.random.choice(
        ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI',
         'NJ', 'VA', 'WA', 'AZ', 'MA', '其他'],
        size=n_samples,
        p=[0.12, 0.08, 0.08, 0.06, 0.05, 0.04, 0.04, 0.04, 0.03, 0.03,
           0.03, 0.03, 0.03, 0.03, 0.03, 0.28]
    )

    # ---- 生成标签: loan_status (是否坏客户) ----
    # 真实的风险因子:
    # FICO分数低 -> 风险高
    # DTI高 -> 风险高
    # 查询次数多 -> 风险高
    # 历史逾期多 -> 风险高
    # 循环利用率高 -> 风险高
    # 短期限 -> 风险高 (36个月比60个月风险高)

    log_odds = (
        - 2.0                                          # 截距 (控制base坏账率)
        - (fico - 700) / 50 * 1.5                      # FICO每低50分, log-odds降低1.5
        + (dti - 15) / 10 * 0.8                        # DTI每高10%, log-odds增加0.8
        + (inquiries_6m - 2) * 0.4                     # 每次查询增加0.4
        + (delinq_2yrs - 0) * 0.7                      # 每次逾期增加0.7
        + (revol_util - 30) / 20 * 0.5                 # 循环利用率每高20%, 增加0.5
        + np.where(term == 36, 0.3, 0)                 # 36个月比60个月风险高
        - (annual_inc - 50000) / 30000 * 0.3           # 收入越高风险越低
        - (credit_age_years - 5) / 5 * 0.3             # 信用越长风险越低
        + np.random.normal(0, 0.5, n_samples)          # 随机扰动
    )

    prob_bad = 1 / (1 + np.exp(-log_odds))
    target = (np.random.random(n_samples) < prob_bad).astype(int)

    # 实际坏账率约8-12% (参照真实Lending Club)
    actual_bad_rate = target.mean()
    print(f"[INFO] 合成数据坏账率: {actual_bad_rate:.2%}")
    print(f"[INFO] 真实Lending Club坏账率参考: 10-15%")

    # 构建DataFrame
    df = pd.DataFrame({
        'loan_amnt': loan_amnt,
        'term': term,
        'int_rate': np.round(np.random.beta(2, 3, n_samples) * 20 + 5, 2),
        'annual_inc': annual_inc,
        'dti': dti,
        'fico_range_low': fico,
        'fico_range_high': fico + np.random.randint(0, 5, n_samples),
        'credit_age_years': credit_age_years,
        'revol_util': revol_util,
        'inq_last_6mths': inquiries_6m,
        'delinq_2yrs': delinq_2yrs,
        'pub_rec': pub_rec,
        'purpose': purpose,
        'home_ownership': home_ownership,
        'emp_length': emp_length,
        'addr_state': addr_state,
        'issue_d': [datetime(2018, 1, 1) + timedelta(days=np.random.randint(0, 720))
                     for _ in range(n_samples)],
        'loan_status': ['Bad' if t == 1 else 'Good' for t in target],
        'target': target,
    })

    # 保存
    save_path = os.path.join(DATA_RAW, "loan_data_synthetic.csv")
    df.to_csv(save_path, index=False)
    print(f"[OK] 合成数据已保存: {save_path}")
    return save_path


def load_raw_data(use_synthetic=True):
    """加载原始数据 (真实数据下载可能因网络问题失败, 默认用合成数据)

    教学说明:
    - 合成数据的变量结构和分布完全参照真实Lending Club数据
    - 在真实公司里,如果你入职后拿不到生产数据,用合成数据验证方法论是完全合理的
    - 面试中: '如果没有真实数据你怎么验证模型方案?'
      答案: 用合成数据验证方法论正确性,然后用真实数据校准参数
    """
    if not use_synthetic:
        path = download_lending_club_data()
        if path is not None:
            df = pd.read_csv(path, low_memory=False)
            print(f"[OK] 真实数据加载完成: {df.shape[0]:,} 行 x {df.shape[1]} 列")
            return df

    path = generate_synthetic_data()

    df = pd.read_csv(path, low_memory=False)
    print(f"[OK] 数据加载完成: {df.shape[0]:,} 行 x {df.shape[1]} 列")
    return df


def create_risk_database(df):
    """
    在SQLite中建立风控核心表结构

    真实公司里的风控数仓一般有三张核心表:
    1. apply_table  (申请表) — 借款人申请时的信息快照
    2. loan_table   (借据表) — 放款后的借据信息
    3. repayment_table (还款表) — 每期还款明细

    面试常问: '风控数据仓库怎么设计?有哪些核心表?'
    答案: 就是这三张表为核心的星型模型
    """
    conn = sqlite3.connect(DB_PATH)
    print(f"[INFO] 创建风控数据库: {DB_PATH}")

    # ---- 1. 申请表 (Application Table) ----
    # 这是借款人提交申请时的"快照"数据
    # 特点: 同一借款人多次申请会有多条记录
    # 面试考点: 为什么用快照而不是实时数据?
    # 答: 因为审批决策必须基于申请时刻的信息,之后的变化不能用来回溯评估
    conn.execute("""
        CREATE TABLE IF NOT EXISTS apply_table (
            application_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id       INTEGER NOT NULL,       -- 借款人ID
            apply_date      DATE NOT NULL,           -- 申请日期
            loan_amnt       REAL,                    -- 申请金额
            term            INTEGER,                 -- 申请期限(月)
            purpose         TEXT,                    -- 借款目的
            annual_inc      REAL,                    -- 年收入
            dti             REAL,                    -- 负债收入比
            fico_score      INTEGER,                 -- FICO信用分
            credit_age      REAL,                    -- 信用历史(年)
            revol_util      REAL,                    -- 循环额度利用率
            inq_6m          INTEGER,                 -- 近6月查询次数
            delinq_2yrs     INTEGER,                 -- 近2年逾期次数
            pub_rec         INTEGER,                 -- 违约记录
            home_ownership  TEXT,                    -- 房屋状态
            emp_length      TEXT,                    -- 工作年限
            addr_state      TEXT,                    -- 所在州
            decision        TEXT DEFAULT 'Pending',  -- 审批结果
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---- 2. 借据表 (Loan Table) ----
    # 审批通过后生成借据
    # 特点: 只关注最终放款的订单
    conn.execute("""
        CREATE TABLE IF NOT EXISTS loan_table (
            loan_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id  INTEGER NOT NULL,
            member_id       INTEGER NOT NULL,
            issue_date      DATE NOT NULL,           -- 放款日期
            loan_amnt       REAL,                    -- 实际放款金额
            term            INTEGER,                 -- 期限(月)
            int_rate        REAL,                    -- 利率
            installment     REAL,                    -- 月还款额
            grade           TEXT,                    -- 风险等级 (A/B/C/D/E)
            fico_score      INTEGER,
            loan_status     TEXT,                    -- 当前状态
            last_pymnt_date DATE,                    -- 最后还款日
            total_pymnt     REAL DEFAULT 0,          -- 累计还款额
            outstanding_principal REAL,              -- 剩余本金
            FOREIGN KEY (application_id) REFERENCES apply_table(application_id)
        )
    """)

    # ---- 3. 还款表 (Repayment Table) ----
    # 每笔借据的每期还款记录
    # 面试考点: 一张借据(loan)对应多笔还款记录(repayment)
    # 通过这张表计算: 逾期天数(DPD), 累计还款额, 提前还款
    conn.execute("""
        CREATE TABLE IF NOT EXISTS repayment_table (
            repayment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id         INTEGER NOT NULL,
            schedule_date   DATE NOT NULL,           -- 计划还款日
            actual_date     DATE,                    -- 实际还款日
            schedule_amt    REAL,                    -- 计划还款金额
            actual_amt      REAL DEFAULT 0,          -- 实际还款金额
            dpd             INTEGER DEFAULT 0,       -- 当前逾期天数
            status          TEXT DEFAULT 'OnTime',   -- 还款状态
            FOREIGN KEY (loan_id) REFERENCES loan_table(loan_id)
        )
    """)

    # ---- 导入数据到库 ----
    # 模拟: 从原始数据中抽取字段填充三张表
    print("[INFO] 导入数据到风控数据库 (模拟数仓ETL)...")

    # 申请表 (所有记录)
    apply_df = df.copy()
    apply_df['application_id'] = range(1, len(apply_df) + 1)
    apply_df['member_id'] = apply_df['application_id']
    apply_df['apply_date'] = pd.to_datetime(apply_df['issue_d'])
    apply_df['fico_score'] = apply_df['fico_range_low']
    apply_df['credit_age'] = apply_df['credit_age_years']
    apply_df['inq_6m'] = apply_df['inq_last_6mths']
    apply_df['decision'] = apply_df['loan_status'].map(
        {'Good': 'Approved', 'Bad': 'Approved'})  # 简化: 所有申请都通过

    apply_cols = ['application_id', 'member_id', 'apply_date', 'loan_amnt',
                  'term', 'purpose', 'annual_inc', 'dti', 'fico_score',
                  'credit_age', 'revol_util', 'inq_6m', 'delinq_2yrs',
                  'pub_rec', 'home_ownership', 'emp_length', 'addr_state',
                  'decision']
    apply_df[apply_cols].to_sql('apply_table', conn, if_exists='replace', index=False)
    print(f"  申请表: {len(apply_df)} 条")

    # 借据表 (仅已放款 = 所有通过的)
    loan_df = apply_df[apply_df['decision'] == 'Approved'].copy()
    loan_df['loan_id'] = range(1, len(loan_df) + 1)
    loan_df['issue_date'] = loan_df['apply_date']
    loan_df['int_rate'] = df.loc[loan_df.index, 'int_rate']
    loan_df['installment'] = (loan_df['loan_amnt'] * 0.03).round(2)  # 简化估算
    loan_df['grade'] = 'C'  # 默认,后面模型会重新评
    loan_df['last_pymnt_date'] = loan_df['issue_date']

    loan_cols = ['loan_id', 'application_id', 'member_id', 'issue_date',
                 'loan_amnt', 'term', 'int_rate', 'installment', 'grade',
                 'fico_score', 'loan_status']
    # loan_status 从 df 映射
    loan_df['loan_status'] = df.loc[loan_df.index, 'loan_status'].values
    loan_df[loan_cols].to_sql('loan_table', conn, if_exists='replace', index=False)
    print(f"  借据表: {len(loan_df)} 条")

    # 还款表 (为每笔借据生成还款计划)
    repayment_rows = []
    for _, loan in loan_df.iterrows():
        n_months = min(int(loan['term']), 12)  # 取前12期(表现期内)
        for m in range(1, n_months + 1):
            schedule_date = pd.to_datetime(loan['issue_date']) + pd.DateOffset(months=m)
            actual_date = schedule_date  # 好人按时还,坏人逾期模拟
            dpd = 0
            status = 'OnTime'
            # 坏客户: 随机产生逾期
            if loan['loan_status'] == 'Bad' and m >= 3:
                if np.random.random() < 0.6:
                    dpd = np.random.choice([30, 60, 90, 120], p=[0.3, 0.3, 0.2, 0.2])
                    status = f'DPD{dpd}'
                    actual_date = schedule_date + pd.DateOffset(days=dpd)

            repayment_rows.append({
                'loan_id': loan['loan_id'],
                'schedule_date': schedule_date.strftime('%Y-%m-%d'),
                'actual_date': actual_date.strftime('%Y-%m-%d'),
                'schedule_amt': round(loan['installment'], 2),
                'actual_amt': round(loan['installment'] * np.random.uniform(0.9, 1.1), 2),
                'dpd': dpd,
                'status': status,
            })

    repayment_df = pd.DataFrame(repayment_rows)
    repayment_df.to_sql('repayment_table', conn, if_exists='replace', index=False)
    print(f"  还款表: {len(repayment_df)} 条")

    conn.commit()
    conn.close()
    print("[OK] 风控数据库创建完成!")
    return DB_PATH


def run_sql(sql):
    """执行查询并返回DataFrame — 模拟在数仓中写SQL取数"""
    conn = sqlite3.connect(DB_PATH)
    result = pd.read_sql_query(sql, conn)
    conn.close()
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("  信用评分卡项目 - 数据加载模块")
    print("=" * 60)
    df = load_raw_data()
    create_risk_database(df)
    print("\n[OK] Phase 1 数据基础准备完成!")
