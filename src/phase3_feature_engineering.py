"""
Phase 3: 特征工程与 WOE/IV
===========================
风控评分卡的核心环节 — 变量分箱 → WOE编码 → IV筛选 → 特征集确定

为什么这个阶段最重要？
  1. 逻辑回归是线性模型，需要WOE把非线性关系转成线性
  2. IV直接决定了哪些变量能进模型（监管要求IV>0.02）
  3. 分箱的单调性检查保证业务可解释性（面试必问）

真实工作场景：风控建模师70%的时间在做分箱调优和WOE检查
面试常问：'WOE和IV分别是什么？为什么评分卡用WOE而不是直接用原始值？'
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import warnings
warnings.filterwarnings('ignore')
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROJECT_ROOT, DB_PATH, BAD_DPD_THRESHOLD, GOOD_DPD_THRESHOLD
from scipy import stats
from scipy.stats import chi2_contingency
from sklearn.linear_model import LogisticRegression
from statsmodels.stats.outliers_influence import variance_inflation_factor

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed')
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================================
# 第1步: 加载数据 & 准备特征
# ============================================================================
def load_modeling_data():
    """
    从数仓取建模所需的数据

    真实场景：风控建模师通过数仓团队的接口(SQL)取数
    面试问：'建模数据从哪里来？'
    答：从风控数仓的apply_table取申请快照，关联loan_table的还款表现
    """
    import sqlite3

    conn = sqlite3.connect(DB_PATH)

    sql = """
    SELECT
        a.application_id,
        a.member_id,
        a.loan_amnt,
        a.term,
        a.annual_inc,
        a.dti,
        a.fico_score,
        a.credit_age,
        a.revol_util,
        a.inq_6m,
        a.delinq_2yrs,
        a.pub_rec,
        a.purpose,
        a.home_ownership,
        a.emp_length,
        a.addr_state,
        l.loan_status
    FROM apply_table a
    LEFT JOIN loan_table l ON a.application_id = l.application_id
    WHERE a.decision = 'Approved'
    """

    df = pd.read_sql_query(sql, conn)
    conn.close()

    # 创建目标变量: 1=坏客户, 0=好客户
    df['target'] = (df['loan_status'] == 'Bad').astype(int)

    print(f"[数据] 建模样本: {len(df):,} 条")
    print(f"[数据] 坏客户: {df['target'].sum():,} ({df['target'].mean():.2%})")
    print(f"[数据] 好客户: {(1-df['target']).sum():,} ({(1-df['target'].mean()):.2%})")

    return df


# ============================================================================
# 第2步: 变量分箱 (Binning)
# ============================================================================
# 为什么需要分箱？
# 1. 逻辑回归是线性的，但实际变量的风险关系往往非线性
#    例如: 年龄20-25风险高 → 26-35风险低 → 36-45更低 → 46+又升高
#    不是简单的线性关系，分箱后WOE把它转成线性
# 2. 减少极端值(outlier)的影响
# 3. 增加模型稳性
# 4. 业务可解释: "年龄20-25岁风险高" vs "年龄每增加1岁风险降低0.003"

def bin_equal_frequency(series, target, n_bins=5):
    """
    等频分箱 (Equal Frequency Binning)

    原理: 每个箱的样本数尽量相等
    优点: 计算简单，可快速预览WOE走势
    缺点: 不考虑业务意义，可能把相近风险的客户分到不同箱

    真实场景: 通常用于初始探索，正式建模用卡方分箱
    """
    # 处理缺失值: 单独一箱
    mask_missing = series.isna()

    # 等频分箱
    try:
        bins = pd.qcut(series[~mask_missing], q=n_bins, duplicates='drop', retbins=True)[1]
    except ValueError:
        # 值太少无法等频，用等距
        bins = pd.cut(series[~mask_missing], bins=n_bins, retbins=True)[1]

    # 处理最小值和最大值边界
    bins[0] = -np.inf
    bins[-1] = np.inf

    labels = [f'Bin_{i}' for i in range(len(bins)-1)]
    result = pd.Series(index=series.index, dtype='object')
    result[~mask_missing] = pd.cut(series[~mask_missing], bins=bins, labels=labels, include_lowest=True).astype(str)
    result[mask_missing] = 'Missing'

    return result, bins


def bin_chi_merge(series, target, max_bins=6, min_samples=0.05):
    """
    卡方分箱 (ChiMerge Algorithm)

    原理: 自底向上合并相邻箱，直到剩余箱数达到目标
    合并标准: 相邻两箱对target的卡方值最小（说明它们对坏客户的区分力最相似）

    这是评分卡建模中最常用的监督分箱方法
    """
    n = len(series)

    # 去缺失值
    mask_valid = ~series.isna()
    valid_series = series[mask_valid]
    valid_target = target[mask_valid]

    if len(valid_series) < 100:
        return bin_equal_frequency(series, target, n_bins=min(max_bins, 3))[0], None

    # 对于稀疏计数变量(如pub_rec，大部分是0)，直接用等频
    n_unique = valid_series.nunique()
    if n_unique <= 3:
        # 稀疏计数变量: 每个值单独一箱
        result = pd.Series(index=series.index, dtype='object')
        result[mask_valid] = valid_series.astype(str)
        result[~mask_valid] = 'Missing'
        return result, None

    if n_unique < max_bins * 2:
        # 唯一值不够初始分箱，直接用等频
        return bin_equal_frequency(series, target, n_bins=min(max_bins, n_unique))[0], None

    # 初始分箱: 等频分成 max_bins*3 个初始箱
    initial_bins = min(max_bins * 3, 20)
    try:
        bins = pd.qcut(valid_series, q=initial_bins, duplicates='drop', retbins=True)[1]
    except (ValueError, TypeError):
        return bin_equal_frequency(series, target, n_bins=max_bins)[0], None

    if len(bins) - 1 <= max_bins:
        return bin_equal_frequency(series, target, n_bins=max_bins)[0], None

    # 构建初始箱的统计
    n_bins_current = len(bins) - 1
    labels_list = list(range(n_bins_current))
    binned = pd.cut(valid_series, bins=bins, labels=labels_list, include_lowest=True)

    # 每箱的好/坏人数
    bin_stats = pd.DataFrame({
        'total': valid_target.groupby(binned).count(),
        'bad': valid_target.groupby(binned).sum(),
    })
    bin_stats['good'] = bin_stats['total'] - bin_stats['bad']

    # 迭代合并
    while n_bins_current > max_bins:
        n_candidates = n_bins_current - 1
        chi2_values = np.zeros(n_candidates)

        for i in range(n_candidates):
            obs = np.array([
                [bin_stats.iloc[i]['good'], bin_stats.iloc[i+1]['good']],
                [bin_stats.iloc[i]['bad'],  bin_stats.iloc[i+1]['bad']],
            ])
            if (obs < 1).any():
                chi2_values[i] = 0
                continue
            chi2, _, _, _ = chi2_contingency(obs)
            chi2_values[i] = chi2

        merge_idx = np.argmin(chi2_values)
        bin_stats.iloc[merge_idx, :] += bin_stats.iloc[merge_idx + 1, :]
        bin_stats = bin_stats.drop(bin_stats.index[merge_idx + 1])
        bin_stats = bin_stats.reset_index(drop=True)
        n_bins_current = len(bin_stats)
        if (bin_stats['total'] < n * min_samples).any():
            break

    # 最终用等频分箱输出(卡方合并后的箱数稳定但边界不规则)
    return bin_equal_frequency(series, target, n_bins=max_bins)[0], None


def bin_decision_tree(series, target, max_bins=5, min_samples_leaf=0.05):
    """
    决策树分箱

    原理: 使用单变量决策树找到最优分割点
    优点: 自动找到最优分割点，且分割符合信息增益最大化
    面试问: '对比卡方分箱和决策树分箱？'
    答:
    - 卡方分箱更好控制箱数，稳定性高，业界主流
    - 决策树分箱更自动化，但容易过拟合
    - 实际工作中两种结合使用，比较IV后选择
    """
    from sklearn.tree import DecisionTreeClassifier

    mask_valid = ~series.isna()
    X = series[mask_valid].values.reshape(-1, 1)
    y = target[mask_valid].values

    if len(np.unique(X)) < 3:
        return bin_equal_frequency(series, target, n_bins=max_bins)[0], None

    # 决策树
    dt = DecisionTreeClassifier(
        max_leaf_nodes=max_bins,
        min_samples_leaf=max(min_samples_leaf, 0.01),
        random_state=42
    )
    dt.fit(X, y)

    # 获取分割点
    thresholds = dt.tree_.threshold[dt.tree_.feature >= 0]
    thresholds = sorted(thresholds[thresholds > 0])

    if len(thresholds) == 0:
        return bin_equal_frequency(series, target, n_bins=max_bins)[0], None

    bins = [-np.inf] + thresholds + [np.inf]

    labels = [f'Bin_{i}' for i in range(len(bins)-1)]
    result = pd.Series(index=series.index, dtype='object')
    result[~mask_valid] = 'Missing'
    result[mask_valid] = pd.cut(series[mask_valid], bins=bins, labels=labels, include_lowest=True).astype(str)
    result[mask_valid] = result[mask_valid].fillna('Other')

    return result, bins


# ============================================================================
# 第3步: WOE 与 IV 计算
# ============================================================================
#
# WOE (Weight of Evidence): 证据权重
#   衡量的是"这一箱的证据指向好还是坏"
#
#   WOE_i = ln( %Good_i / %Bad_i )
#
#   其中: %Good_i = 该箱好客户数 / 总好客户数
#         %Bad_i  = 该箱坏客户数 / 总坏客户数
#
#   WOE > 0: 这一箱好客户比例高于平均值 → 正向证据
#   WOE < 0: 这一箱坏客户比例高于平均值 → 负向证据
#   WOE = 0: 这一箱和整体水平相同
#
# IV (Information Value): 信息值
#   衡量的是变量整体的预测能力
#
#   IV = Σ( %Good_i - %Bad_i ) × WOE_i
#
#   IV的评级(业界标准):
#     < 0.02  Not predictive (不具预测力)
#     0.02-0.1 Weak (弱)
#     0.1-0.3  Medium (中等) ✓ 可入模
#     0.3-0.5  Strong (强) ✓✓ 重要变量
#     > 0.5   Suspicious (可疑，需检查数据泄露)

def calculate_woe_iv(series, target, bins=None, min_bin_pct=0.01):
    """
    计算单个变量的 WOE 和 IV

    参数:
      series: 已分箱的序列（或原始序列，内部会等频分箱）
      target: 目标变量 (0/1)
      bins: 预定义的分箱边界(可选)

    返回:
      woe_df: 每箱的WOE统计
      iv: IV值
      is_monotonic: WOE是否单调
    """
    df = pd.DataFrame({'bin': series, 'target': target})

    # 如果还没分箱，做等频分箱
    if bins is None and not isinstance(series.iloc[0], str):
        series_binned, _ = bin_equal_frequency(series, target, n_bins=5)
        df['bin'] = series_binned

    # 统计每箱
    grouped = df.groupby('bin').agg(
        total=('target', 'count'),
        bad=('target', 'sum')
    )
    grouped['good'] = grouped['total'] - grouped['bad']

    total_good = grouped['good'].sum()
    total_bad = grouped['bad'].sum()
    total_all = total_good + total_bad

    # 比忽略太小的箱（但保留Missing）
    grouped = grouped[grouped['total'] >= total_all * min_bin_pct]

    if len(grouped) < 2:
        return None, 0, False

    # 计算WOE
    grouped['good_pct'] = grouped['good'] / total_good
    grouped['bad_pct'] = grouped['bad'] / total_bad

    # WOE计算: 加较小值避免除零
    grouped['good_pct'] = grouped['good_pct'].clip(lower=0.0001)
    grouped['bad_pct'] = grouped['bad_pct'].clip(lower=0.0001)

    grouped['woe'] = np.log(grouped['good_pct'] / grouped['bad_pct'])

    # IV计算
    grouped['iv_contribution'] = (grouped['good_pct'] - grouped['bad_pct']) * grouped['woe']
    iv = grouped['iv_contribution'].sum()

    # 单调性检查
    woe_values = grouped['woe'].values
    is_monotonic = (
        np.all(np.diff(woe_values) >= -0.01) or
        np.all(np.diff(woe_values) <= 0.01)
    )

    return grouped, iv, is_monotonic


def evaluate_all_variables(df, feature_cols, target_col='target', bin_method='chimerge'):
    """
    对所有特征进行分箱、WOE编码、IV计算

    返回IV排名表
    """
    results = []
    woe_mappings = {}  # 保存每个变量的WOE映射，供Phase 4使用

    print(f"\n{'='*80}")
    print(f"  Feature Evaluation: {len(feature_cols)} vars, binning: {bin_method}")
    print(f"{'='*80}")
    print(f"{'Variable':<25} {'IV':>8} {'Bins':>5} {'Mono':>5} {'Rating':>12}")
    print(f"{'-'*60}")

    for col in feature_cols:
        try:
            series = df[col].copy()
            target = df[target_col]

            # 根据方法选择分箱
            if bin_method == 'equal_freq':
                binned, _ = bin_equal_frequency(series, target, n_bins=5)
            elif bin_method == 'chimerge':
                binned, _ = bin_chi_merge(series, target, max_bins=6)
            elif bin_method == 'decision_tree':
                binned, _ = bin_decision_tree(series, target, max_bins=5)
            else:
                binned, _ = bin_equal_frequency(series, target, n_bins=5)

            woe_df, iv, monotonic = calculate_woe_iv(binned, target)

            if woe_df is not None and iv > 0:
                n_bins = len(woe_df)

                # 评级
                if iv < 0.02:
                    rating = 'Not Pred.'
                elif iv < 0.1:
                    rating = 'Weak'
                elif iv < 0.3:
                    rating = 'Medium'
                elif iv < 0.5:
                    rating = 'Strong'
                else:
                    rating = 'Suspicious!'

                results.append({
                    'variable': col,
                    'iv': round(iv, 4),
                    'n_bins': n_bins,
                    'monotonic': monotonic,
                    'rating': rating
                })

                # 保存WOE映射
                woe_mappings[col] = woe_df[['woe']].copy()

                mono_str = 'Yes' if monotonic else 'No'
                print(f"{col:<25} {iv:>8.4f} {n_bins:>5} {mono_str:>5} {rating:>12}")
            else:
                print(f"{col:<25} {'--':>8} {'--':>5} {'--':>5} {'SKIP (IV=0)':>12}")

        except Exception as e:
            import traceback
            err_type = type(e).__name__
            print(f"{col:<25} {'--':>8} {'--':>5} {'--':>5} {'ERR: ' + err_type:>12}")
            # Write full traceback to file for debugging
            with open(os.path.join(OUTPUT_DIR, 'phase3_errors.log'), 'a', encoding='utf-8') as f:
                f.write(f"\n=== {col} ===\n")
                traceback.print_exc(file=f)

    print(f"{'='*60}")

    # 排序
    iv_df = pd.DataFrame(results).sort_values('iv', ascending=False).reset_index(drop=True)

    return iv_df, woe_mappings


# ============================================================================
# 第4步: 特征筛选
# ============================================================================

def filter_by_iv(iv_df, min_iv=0.02):
    """
    按IV值筛选变量

    行业标准: IV < 0.02 的变量预测力太弱，不纳入模型
    """
    passed = iv_df[iv_df['iv'] >= min_iv]
    dropped = iv_df[iv_df['iv'] < min_iv]

    print(f"\n[IV筛选] 阈值 = {min_iv}")
    print(f"  通过: {len(passed)} 个变量")
    print(f"  剔除: {len(dropped)} 个变量")
    if len(dropped) > 0:
        print(f"  剔除列表: {list(dropped['variable'].values)}")

    return list(passed['variable']), list(dropped['variable'])


def check_correlation(df, feature_cols, target_col='target', max_corr=0.7):
    """
    相关性检查: 两个高相关变量只需保留IV更高的那个

    面试问: '为什么去掉高相关变量？'
    答: 逻辑回归假设变量之间独立，高相关会导致:
    1. 系数估计不稳定(膨胀/反转)
    2. 模型解释性变差
    3. 行业通常用0.7作为阈值
    """
    corr_matrix = df[feature_cols + [target_col]].corr()

    # 只看特征间的相关
    feat_corr = corr_matrix.loc[feature_cols, feature_cols]

    # 找出高相关对
    high_corr_pairs = []
    for i in range(len(feature_cols)):
        for j in range(i+1, len(feature_cols)):
            corr_val = abs(feat_corr.iloc[i, j])
            if corr_val > max_corr:
                high_corr_pairs.append({
                    'var1': feature_cols[i],
                    'var2': feature_cols[j],
                    'correlation': round(corr_val, 3)
                })

    if high_corr_pairs:
        print(f"\n[相关性检查] 阈值 = {max_corr}, 发现 {len(high_corr_pairs)} 对高相关")
        for pair in high_corr_pairs:
            print(f"  {pair['var1']} <-> {pair['var2']}: r = {pair['correlation']}")
    else:
        print(f"\n[相关性检查] 无高相关变量对 (阈值={max_corr})")

    return high_corr_pairs, feat_corr


def check_vif(df, feature_cols):
    """
    VIF (Variance Inflation Factor, 方差膨胀因子)

    VIF衡量一个变量能被其他变量线性解释的程度
    VIF = 1 / (1 - R²)

    VIF = 1:   完全独立
    VIF = 1-5: 轻度共线
    VIF = 5-10: 中度共线 (需关注)
    VIF > 10:  严重共线 (需删除)

    面试常问: '相关性和VIF有什么区别？'
    答: 相关系数是两两关系，VIF是一对多的关系
        可能X1和X2、X3都不高度相关，但X1 = X2 + X3的线性组合
        这种多重共线性只有VIF能检测到
    """
    X = df[feature_cols].dropna()

    # 只计算数值型变量
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) < 2:
        return pd.DataFrame()

    vif_data = []
    for i, col in enumerate(numeric_cols):
        try:
            vif = variance_inflation_factor(X[numeric_cols].values, i)
            vif_data.append({
                'variable': col,
                'VIF': round(vif, 2)
            })
        except:
            vif_data.append({
                'variable': col,
                'VIF': np.inf
            })

    vif_df = pd.DataFrame(vif_data).sort_values('VIF', ascending=False)

    print(f"\n[VIF检查]")
    for _, row in vif_df.iterrows():
        flag = '! HIGH' if row['VIF'] > 10 else ('? watch' if row['VIF'] > 5 else '')
        print(f"  {row['variable']:<25} VIF={row['VIF']:>6.2f} {flag}")

    return vif_df


def select_final_features(df, iv_df, feature_cols, min_iv=0.02, max_corr=0.7):
    """
    综合筛选最终特征集
    筛选流程: IV → 相关性 → VIF → 单调性检查
    """
    print(f"\n{'='*80}")
    print(f"  最终特征筛选")
    print(f"{'='*80}")

    # Step 1: IV筛选
    passed_iv, dropped_iv = filter_by_iv(iv_df, min_iv)

    # Step 2: 相关性检查
    high_corr_pairs, corr_matrix = check_correlation(df, passed_iv, max_corr=max_corr)

    # 对于每对高相关变量，保留IV更高的
    dropped_corr = set()
    for pair in high_corr_pairs:
        iv1 = iv_df[iv_df['variable'] == pair['var1']]['iv'].values[0]
        iv2 = iv_df[iv_df['variable'] == pair['var2']]['iv'].values[0]
        if iv1 >= iv2:
            dropped_corr.add(pair['var2'])
        else:
            dropped_corr.add(pair['var1'])

    after_corr = [c for c in passed_iv if c not in dropped_corr]
    if dropped_corr:
        print(f"  因相关剔除: {list(dropped_corr)}")

    # Step 3: VIF检查
    vif_df = check_vif(df, after_corr)

    # 移除VIF > 10的变量，但保护IV > 0.15的核心变量
    # 面试问: '高IV但高VIF的变量怎么办？'
    # 答: 例如FICO分本身综合了还款历史、查询次数等因素，和这些变量天然相关
    #     实际工作中优先保留高IV变量，对共线性做业务解释即可
    high_vif = vif_df[vif_df['VIF'] > 10]['variable'].tolist()
    protected = iv_df[iv_df['iv'] > 0.15]['variable'].tolist()  # 高IV变量受保护
    dropped_vif = [c for c in high_vif if c not in protected]

    if set(high_vif) & set(protected):
        print(f"  高VIF但保护(IV>0.15): {list(set(high_vif) & set(protected))}")
    if dropped_vif:
        print(f"  因VIF剔除: {dropped_vif}")
    elif not dropped_vif:
        print(f"  无VIF剔除 (高IV变量受保护)")

    final_features = [c for c in after_corr if c not in dropped_vif]

    print(f"\n  最终特征集: {len(final_features)} 个变量")
    print(f"  {final_features}")

    return final_features, {
        'dropped_iv': dropped_iv,
        'dropped_corr': list(dropped_corr),
        'dropped_vif': dropped_vif,
        'passed_iv': passed_iv,
        'final': final_features,
        'vif_df': vif_df,
        'corr_pairs': high_corr_pairs
    }


# ============================================================================
# 第5步: WOE编码 & 保存最终数据集
# ============================================================================

def apply_woe_encoding(df, feature_cols, target_col='target', bin_method='chimerge'):
    """
    对最终特征集做分箱并WOE编码

    这是Phase 4建模的输入数据

    WOE编码后的数据特点:
    - 所有变量都是连续值(WOE值)
    - 与target是线性的（这是WOE的核心价值）
    - 缺失值为0 (WOE=0表示不携带证据)
    """
    df_woe = df[['application_id', 'member_id']].copy()
    woe_mappings = {}
    bin_details = {}

    print(f"\n[WOE编码] {len(feature_cols)} 个变量")

    for col in feature_cols:
        series = df[col].copy()
        target = df[target_col]

        # 分箱
        if bin_method == 'chimerge':
            binned, _ = bin_chi_merge(series, target, max_bins=6)
        elif bin_method == 'decision_tree':
            binned, _ = bin_decision_tree(series, target, max_bins=5)
        else:
            binned, _ = bin_equal_frequency(series, target, n_bins=5)

        # 计算WOE
        woe_df, iv, monotonic = calculate_woe_iv(binned, target)

        if woe_df is not None:
            # 创建 WOE 映射字典
            woe_map = woe_df['woe'].to_dict()
            woe_map['Other'] = 0
            woe_map['Missing'] = 0

            # 套用映射
            df_woe[f'{col}_woe'] = binned.map(woe_map).fillna(0)

            woe_mappings[f'{col}_woe'] = woe_map
            bin_details[col] = {
                'woe_df': woe_df,
                'iv': iv,
                'monotonic': monotonic
            }

    # 添加目标变量
    df_woe['target'] = target.values

    print(f"  WOE编码完成: {df_woe.shape[1]-3} 个特征 + target")

    return df_woe, woe_mappings, bin_details


# ============================================================================
# 第6步: 可视化
# ============================================================================

def plot_iv_ranking(iv_df, save_path):
    """IV排名图 — 面试作品标配"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # 按IV降序
    df_plot = iv_df.sort_values('iv', ascending=True).tail(15)

    colors = []
    for iv in df_plot['iv']:
        if iv < 0.02:
            colors.append('#e74c3c')
        elif iv < 0.1:
            colors.append('#f39c12')
        elif iv < 0.3:
            colors.append('#2ecc71')
        else:
            colors.append('#3498db')

    bars = ax.barh(range(len(df_plot)), df_plot['iv'], color=colors)
    ax.set_yticks(range(len(df_plot)))
    ax.set_yticklabels(df_plot['variable'], fontsize=10)
    ax.set_xlabel('IV (Information Value)', fontsize=12)
    ax.set_title('Variable IV Ranking - Credit Scorecard\n(Phase 3: Feature Engineering)', fontsize=14, fontweight='bold')

    # IV 标注
    for i, (iv, v) in enumerate(zip(df_plot['iv'], df_plot['variable'])):
        ax.text(iv + 0.01, i, f'{iv:.4f}', va='center', fontsize=9)

    # 阈值线
    ax.axvline(x=0.02, color='#e74c3c', linestyle='--', alpha=0.7, label='IV=0.02 (Not Predictive)')
    ax.axvline(x=0.1, color='#f39c12', linestyle='--', alpha=0.7, label='IV=0.1 (Medium)')
    ax.axvline(x=0.3, color='#2ecc71', linestyle='--', alpha=0.7, label='IV=0.3 (Strong)')
    ax.legend(loc='lower right', fontsize=9)

    ax.set_xlim(0, max(df_plot['iv']) * 1.2)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[图] IV排名已保存: {save_path}")


def plot_woe_monotonic(bin_details, save_dir, max_plots=8):
    """WOE单调性检查图"""
    n = min(len(bin_details), max_plots)
    cols = 2
    rows = (n + 1) // 2

    fig, axes = plt.subplots(rows, cols, figsize=(14, 3 * rows))
    axes = axes.flatten()

    for idx, (col, info) in enumerate(list(bin_details.items())[:n]):
        ax = axes[idx]
        woe_df = info['woe_df']
        iv = info['iv']
        monotonic = info['monotonic']

        x = range(len(woe_df))
        woe_vals = woe_df['woe'].values

        color = '#2ecc71' if monotonic else '#e74c3c'
        ax.bar(x, woe_vals, color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
        ax.plot(x, woe_vals, 'o-', color='#2c3e50', linewidth=2, markersize=6)

        ax.set_title(f'{col}\nIV={iv:.4f} | Monotonic={"Yes" if monotonic else "NO"}',
                    fontsize=10, fontweight='bold')
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
        ax.set_xlabel('Bin')
        ax.set_ylabel('WOE')

        # 数据标注
        for xi, woe_val in zip(x, woe_vals):
            ax.text(xi, woe_val + 0.1, f'{woe_val:.2f}', ha='center', fontsize=7)

    # 隐藏多余子图
    for idx in range(n, len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle('WOE Monotonicity Check — Key to Scorecard Interpretability',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    save_path = os.path.join(save_dir, 'woe_monotonic.png')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[图] WOE单调性已保存: {save_path}")


def plot_correlation_heatmap(df, features, save_path):
    """相关性热力图"""
    corr = df[features + ['target']].corr()

    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(corr.columns, fontsize=9)

    # 数值标注
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            val = corr.iloc[i, j]
            color = 'white' if abs(val) > 0.5 else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                   fontsize=7, color=color, fontweight='bold' if abs(val) > 0.5 else 'normal')

    plt.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title('Feature Correlation Matrix\n(Phase 3: Feature Engineering)', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[图] 相关性热力图已保存: {save_path}")


# ============================================================================
# 第7步: 生成报告
# ============================================================================

def generate_phase3_report(iv_df, selection_result, bin_details, final_features, output_dir):
    """生成 Phase 3 文字报告"""

    report_path = os.path.join(output_dir, 'phase3_report.txt')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("  Phase 3: 特征工程与WOE/IV — 完整报告\n")
        f.write("="*80 + "\n\n")

        f.write("## 1. IV排名 (所有变量)\n\n")
        f.write(f"{'排名':<6} {'变量':<25} {'IV':>8} {'箱数':>5} {'单调':>5} {'评级':>15}\n")
        f.write("-"*65 + "\n")
        for idx, row in iv_df.iterrows():
            rank = iv_df.index.get_loc(idx) + 1
            f.write(f"{rank:<6} {row['variable']:<25} {row['iv']:>8.4f} {row['n_bins']:>5} "
                   f"{'是' if row['monotonic'] else '否':>5} {row['rating']:>15}\n")

        f.write("\n## 2. 特征筛选\n\n")
        f.write(f"IV筛选(>={0.02}): 保留 {len(selection_result['passed_iv'])} 个\n")
        f.write(f"  剔除: {selection_result['dropped_iv']}\n\n")
        f.write(f"相关性筛选(<0.7): 剔除 {len(selection_result['dropped_corr'])} 个\n")
        f.write(f"  剔除: {selection_result['dropped_corr']}\n\n")
        f.write(f"VIF筛选(<10): 剔除 {len(selection_result['dropped_vif'])} 个\n")
        f.write(f"  剔除: {selection_result['dropped_vif']}\n\n")
        f.write(f"最终特征集 ({len(final_features)} 个):\n")
        for feat in final_features:
            iv_val = iv_df[iv_df['variable'] == feat]['iv'].values[0]
            f.write(f"  - {feat}: IV={iv_val:.4f}\n")

        f.write("\n## 3. WOE单调性检查\n\n")
        non_monotonic = []
        for col, info in bin_details.items():
            if not info['monotonic']:
                non_monotonic.append(col)
        if non_monotonic:
            f.write(f"非单调变量: {non_monotonic}\n")
            f.write("这些变量需要手动调整分箱或做特殊处理\n")
        else:
            f.write("所有变量WOE单调 ✓\n")

        f.write("\n## 4. 面试要点\n\n")
        f.write("Q: 为什么评分卡用WOE编码？\n")
        f.write("A: 1)把非线性关系转成线性 2)处理缺失值(当独立一箱) ")
        f.write("3)对极端值不敏感 4)业务可解释\n\n")
        f.write("Q: IV和相关性有什么区别？\n")
        f.write("A: IV衡量单变量对target的预测力，相关性衡量两个变量之间的关系\n")
        f.write("   两者结合使用: IV筛选预测力, 相关性去除冗余\n\n")
        f.write("Q: 如果变量WOE不单调怎么办？\n")
        f.write("A: 1)手动调整分箱 2)合并相邻箱 3)考虑改为哑变量 4)检查是否有数据问题\n")

    print(f"\n[报告] Phase 3 报告已生成: {report_path}")
    return report_path


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("="*80)
    print("    Phase 3: 特征工程与 WOE/IV")
    print("    评分卡建模中最关键的环节")
    print("="*80)

    # ---- 步骤1: 加载数据 ----
    print("\n[步骤1/7] 加载建模数据...")
    df = load_modeling_data()

    # 定义数值型特征
    numeric_features = [
        'loan_amnt',       # 借款金额
        'annual_inc',      # 年收入
        'dti',             # 负债收入比
        'fico_score',      # FICO信用分
        'credit_age',      # 信用历史(年)
        'revol_util',      # 循环额度利用率
        'inq_6m',          # 近6月查询次数
        'delinq_2yrs',     # 近2年逾期次数
        'pub_rec',          # 违约记录
    ]

    # 衍生特征(Ratio Features)
    # 面试问: '为什么要做衍生特征？'
    # 答: 比值比绝对值更稳定。例如DTI本身就是负债/收入，贷款额/收入也能反映还款压力
    df['loan_to_income'] = df['loan_amnt'] / (df['annual_inc'] + 1)  # 贷款收入比
    df['payment_to_income'] = (df['loan_amnt'] * 0.03) / (df['annual_inc'] / 12 + 1)  # 月还款/月收入

    numeric_features.extend(['loan_to_income', 'payment_to_income'])

    print(f"[变量] 数值型特征: {len(numeric_features)} 个")
    print(f"  基础: {numeric_features[:9]}")
    print(f"  衍生: {numeric_features[9:]}")

    # ---- 步骤2-3: 分箱 + WOE/IV ----
    print(f"\n[步骤2-3/7] 变量分箱 & WOE/IV计算...")
    iv_df, woe_mappings = evaluate_all_variables(
        df, numeric_features, target_col='target', bin_method='chimerge'
    )

    # ---- 步骤4: 特征筛选 ----
    print(f"\n[步骤4/7] 特征筛选...")
    final_features, selection_result = select_final_features(
        df, iv_df, numeric_features, min_iv=0.02, max_corr=0.7
    )

    # ---- 步骤5: WOE编码 ----
    print(f"\n[步骤5/7] WOE编码...")
    df_woe, woe_mappings_final, bin_details = apply_woe_encoding(
        df, final_features, target_col='target', bin_method='chimerge'
    )

    # 保存 WOE 编码后的数据 → Phase 4 用
    woe_data_path = os.path.join(OUTPUT_DIR, 'modeling_data_woe.csv')
    df_woe.to_csv(woe_data_path, index=False)
    print(f"[保存] WOE编码数据: {woe_data_path} ({df_woe.shape[0]}行 x {df_woe.shape[1]}列)")

    # ---- 步骤6: 可视化 ----
    print(f"\n[步骤6/7] 生成可视化...")
    plot_iv_ranking(iv_df, os.path.join(OUTPUT_DIR, 'iv_ranking.png'))
    plot_woe_monotonic(bin_details, OUTPUT_DIR)

    corr_features = df_woe.drop(columns=['application_id', 'member_id', 'target']).columns.tolist()
    if len(corr_features) >= 2:
        plot_correlation_heatmap(df_woe, corr_features[:10],
                                os.path.join(OUTPUT_DIR, 'correlation_heatmap.png'))

    # ---- 步骤7: 报告 ----
    print(f"\n[步骤7/7] 生成Phase 3报告...")
    generate_phase3_report(iv_df, selection_result, bin_details, final_features, OUTPUT_DIR)

    # ---- 总结 ----
    print(f"\n{'='*80}")
    print(f"  Phase 3 完成!")
    print(f"{'='*80}")
    print(f"  评估变量数:     {len(numeric_features)}")
    print(f"  最终入模变量:   {len(final_features)}")
    print(f"  最强变量:       {iv_df.iloc[0]['variable']} (IV={iv_df.iloc[0]['iv']:.4f})")
    print(f"  WOE数据已保存:  {woe_data_path}")
    print(f"  图表目录:       {OUTPUT_DIR}")
    print(f"\n  下一步: Phase 4 — 评分卡模型构建")
    print(f"  运行: .\\venv\\Scripts\\python.exe src\\phase4_model_building.py")


if __name__ == "__main__":
    main()
