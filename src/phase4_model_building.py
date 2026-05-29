"""
Phase 4: 评分卡模型构建
======================
从WOE编码数据 → 逻辑回归 → 评分卡转换 → 序列化产出物

评分卡转换公式:
  Factor = PDO / ln(2)
  Offset = BASE_SCORE - Factor * ln(BASE_ODDS)
  Score = Offset - Factor * intercept - Factor * sum(coef_i * woe_i)

面试必问: '评分卡的分数字怎么来的?'
答: 逻辑回归输出log(odds), 通过PDO/Base Score做线性变换映射到
    600基准分, 每20分odds翻倍。这样的分数对业务方直观可理解。
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
import os, sys, json, joblib
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    PROJECT_ROOT, DB_PATH, BASE_SCORE, PDO, BASE_ODDS,
    RISK_GRADES, PSI_ALERT, PSI_REBUILD, KS_MIN
)

# Import Phase 3 binning functions
from src.phase3_feature_engineering import (
    load_modeling_data, bin_chi_merge, bin_equal_frequency,
    calculate_woe_iv
)

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'data', 'artifacts')
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Final 7 features from Phase 3
FINAL_FEATURES = [
    'fico_score', 'inq_6m', 'dti', 'revol_util',
    'delinq_2yrs', 'credit_age', 'annual_inc'
]

TRAIN_DATE = datetime.now().strftime('%Y-%m-%d %H:%M')


# ============================================================================
# Step 1: Re-bin features and capture boundaries + WOE maps
# ============================================================================
def build_woe_artifacts(df, feature_cols, target_col='target'):
    """
    Re-run binning on final features, capturing:
    - bin_boundaries: numeric edges for each feature (for inference)
    - woe_maps: {bin_label: woe_value} for each feature
    """
    bin_boundaries = {}
    woe_maps = {}
    iv_table = {}

    print(f"\n[分箱] 为 {len(feature_cols)} 个最终特征构建分箱映射...")

    for col in feature_cols:
        series = df[col].copy()
        target = df[target_col]

        # Use chi-merge binning (same as Phase 3)
        binned, _ = bin_chi_merge(series, target, max_bins=6)

        # Get WOE
        woe_df, iv, monotonic = calculate_woe_iv(binned, target)

        if woe_df is None or len(woe_df) < 2:
            print(f"  [WARN] {col}: WOE计算失败, 跳过")
            continue

        # Build WOE map: {bin_label: woe_value}
        woe_map = woe_df['woe'].to_dict()

        # Build bin boundaries using equal-frequency on the valid values
        mask_valid = ~series.isna()
        valid_vals = series[mask_valid]
        n_bins = len(woe_df)

        if n_bins >= 2:
            try:
                _, boundaries = bin_equal_frequency(series, target, n_bins=n_bins)
                # boundaries from bin_equal_frequency includes -inf and inf
                # For pd.cut compatibility, store as list
                bin_boundaries[col] = [float(b) for b in boundaries]
            except Exception:
                bin_boundaries[col] = None
        else:
            bin_boundaries[col] = None

        woe_maps[col] = woe_map
        iv_table[col] = {'iv': round(iv, 4), 'monotonic': monotonic, 'n_bins': n_bins}
        print(f"  {col}: IV={iv:.4f}, bins={n_bins}, mono={monotonic}")

    return bin_boundaries, woe_maps, iv_table


# ============================================================================
# Step 2: Load WOE data and train logistic regression
# ============================================================================
def train_logistic_regression(woe_csv_path):
    """Train LR on WOE-encoded data"""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    df_woe = pd.read_csv(woe_csv_path)
    print(f"\n[数据] WOE数据: {df_woe.shape[0]}行 x {df_woe.shape[1]}列")

    woe_cols = [c for c in df_woe.columns if c.endswith('_woe')]
    print(f"[特征] WOE特征列: {woe_cols}")

    X = df_woe[woe_cols].values
    y = df_woe['target'].values

    # 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # High C = low regularization (WOE already linearizes)
    lr = LogisticRegression(C=1e6, solver='lbfgs', max_iter=2000, random_state=42)
    lr.fit(X_train, y_train)

    print(f"\n[模型] 逻辑回归训练完成")
    print(f"  Intercept: {lr.intercept_[0]:.6f}")
    for col, coef in zip(woe_cols, lr.coef_[0]):
        print(f"  {col}: {coef:.6f}")

    return lr, woe_cols, X_train, X_test, y_train, y_test


# ============================================================================
# Step 3: Build scorecard
# ============================================================================
def build_scorecard(lr_model, feature_names):
    """
    Convert LR coefficients to scorecard points.

    Score = Offset - Factor * ln(Odds_bad)
          = Offset - Factor * (intercept + sum(coef_i * woe_i))
          = Offset - Factor*intercept - Factor * sum(coef_i * woe_i)

    BasePoints = Offset - Factor * intercept
    FeaturePoints_i(bin) = -Factor * coef_i * woe_i(bin)
    """
    import math

    factor = PDO / math.log(2)
    offset = BASE_SCORE - factor * math.log(BASE_ODDS)

    intercept = float(lr_model.intercept_[0])
    coefficients = {name: float(coef) for name, coef in zip(feature_names, lr_model.coef_[0])}

    base_points = offset - factor * intercept

    params = {
        'factor': round(factor, 6),
        'offset': round(offset, 6),
        'base_score': BASE_SCORE,
        'pdo': PDO,
        'base_odds': BASE_ODDS,
        'intercept': round(intercept, 6),
        'base_points': round(base_points, 4),
        'coefficients': coefficients,
        'feature_names': feature_names,
        'training_date': TRAIN_DATE,
        'model_version': 'v1.0',
    }

    print(f"\n[评分卡] 参数:")
    print(f"  Factor (PDO/ln2): {factor:.4f}")
    print(f"  Offset:            {offset:.4f}")
    print(f"  Intercept:         {intercept:.6f}")
    print(f"  Base Points:       {base_points:.2f}")

    return params


# ============================================================================
# Step 4: Model performance evaluation
# ============================================================================
def evaluate_model(lr_model, X_train, X_test, y_train, y_test, feature_names):
    """Compute AUC, KS, and generate score distributions"""
    from sklearn.metrics import (
        roc_auc_score, confusion_matrix, classification_report,
        roc_curve
    )

    # Predictions
    y_train_prob = lr_model.predict_proba(X_train)[:, 1]
    y_test_prob = lr_model.predict_proba(X_test)[:, 1]
    y_train_pred = lr_model.predict(X_train)
    y_test_pred = lr_model.predict(X_test)

    # AUC
    train_auc = roc_auc_score(y_train, y_train_prob)
    test_auc = roc_auc_score(y_test, y_test_prob)

    # KS statistic
    def compute_ks(y_true, y_prob):
        """KS = max(|cum_good - cum_bad|)"""
        df_ks = pd.DataFrame({'true': y_true, 'prob': y_prob})
        df_ks = df_ks.sort_values('prob', ascending=False)
        df_ks['cum_bad'] = (df_ks['true'] == 1).cumsum() / (df_ks['true'] == 1).sum()
        df_ks['cum_good'] = (df_ks['true'] == 0).cumsum() / (df_ks['true'] == 0).sum()
        ks = max(abs(df_ks['cum_good'] - df_ks['cum_bad']))
        return ks

    train_ks = compute_ks(y_train, y_train_prob)
    test_ks = compute_ks(y_test, y_test_prob)

    print(f"\n[评估] 模型性能:")
    print(f"  Train AUC: {train_auc:.4f}")
    print(f"  Test  AUC: {test_auc:.4f}")
    print(f"  Train KS:  {train_ks:.4f}")
    print(f"  Test  KS:  {test_ks:.4f}")
    print(f"  KS >= {KS_MIN} (最低要求): {'PASS' if test_ks >= KS_MIN else 'FAIL'}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_test_pred)
    print(f"\n  混淆矩阵 (Test):")
    print(f"    TN={cm[0][0]:,}  FP={cm[0][1]:,}")
    print(f"    FN={cm[1][0]:,}  TP={cm[1][1]:,}")

    # Feature importance (coefficient magnitude)
    importance = pd.DataFrame({
        'feature': feature_names,
        'coefficient': [abs(float(c)) for c in lr_model.coef_[0]],
        'raw_coef': [float(c) for c in lr_model.coef_[0]],
    }).sort_values('coefficient', ascending=False)

    print(f"\n  特征重要性 (|coefficient|):")
    for _, row in importance.iterrows():
        print(f"    {row['feature']:<30} |coef|={row['coefficient']:.4f}  coef={row['raw_coef']:.4f}")

    return {
        'train_auc': round(train_auc, 4),
        'test_auc': round(test_auc, 4),
        'train_ks': round(train_ks, 4),
        'test_ks': round(test_ks, 4),
        'confusion_matrix': cm.tolist(),
        'feature_importance': importance.to_dict('records'),
        'y_test_true': y_test.tolist(),
        'y_test_prob': y_test_prob.tolist(),
    }


# ============================================================================
# Step 5: Generate scorecard table (points per bin per feature)
# ============================================================================
def generate_scorecard_table(params, woe_maps):
    """
    Build the complete scorecard table:
    For each feature, for each bin, show the points contributed.
    """
    factor = params['factor']
    coefficients = params['coefficients']
    base_points = params['base_points']

    scorecard_table = {'base_points': round(base_points, 2), 'features': {}}

    for feature_name, woe_map in woe_maps.items():
        coef = coefficients.get(feature_name + '_woe', 0)
        feature_points = {}
        for bin_label, woe_val in woe_map.items():
            pts = -factor * coef * woe_val
            feature_points[bin_label] = round(float(pts), 2)
        scorecard_table['features'][feature_name] = {
            'coefficient': coef,
            'bins': feature_points,
            'woe_map': {k: round(float(v), 4) for k, v in woe_map.items()},
        }

    return scorecard_table


# ============================================================================
# Step 6: Serialize all artifacts
# ============================================================================
def serialize_artifacts(bin_boundaries, woe_maps, lr_model, params, metrics):
    """Save all model artifacts for the API to load"""
    print(f"\n[序列化] 保存模型产出物到 {ARTIFACTS_DIR}")

    # WOE bin maps (for transforming raw features to WOE)
    joblib.dump(bin_boundaries, os.path.join(ARTIFACTS_DIR, 'bin_boundaries.joblib'))
    joblib.dump(woe_maps, os.path.join(ARTIFACTS_DIR, 'woe_maps.joblib'))

    # Logistic regression model
    joblib.dump(lr_model, os.path.join(ARTIFACTS_DIR, 'lr_model.joblib'))

    # Scorecard parameters
    joblib.dump(params, os.path.join(ARTIFACTS_DIR, 'scorecard_params.joblib'))

    # Feature order
    joblib.dump(params['feature_names'], os.path.join(ARTIFACTS_DIR, 'feature_order.joblib'))

    # Performance metrics
    metrics_to_save = {k: v for k, v in metrics.items() if k not in ('y_test_true', 'y_test_prob')}
    with open(os.path.join(ARTIFACTS_DIR, 'model_metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics_to_save, f, indent=2, ensure_ascii=False)

    # Also save the risk grades from config
    joblib.dump(RISK_GRADES, os.path.join(ARTIFACTS_DIR, 'risk_grades.joblib'))

    print(f"  已保存: bin_boundaries.joblib, woe_maps.joblib, lr_model.joblib")
    print(f"  已保存: scorecard_params.joblib, feature_order.joblib")
    print(f"  已保存: model_metrics.json, risk_grades.joblib")


# ============================================================================
# Step 7: Visualization
# ============================================================================
def plot_roc_curve(metrics, save_path):
    """ROC curve"""
    from sklearn.metrics import roc_curve as sk_roc_curve

    fpr, tpr, _ = sk_roc_curve(metrics['y_test_true'], metrics['y_test_prob'])

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, 'b-', linewidth=2, label=f"ROC (AUC={metrics['test_auc']:.4f})")
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Random')
    ax.fill_between(fpr, tpr, alpha=0.1, color='blue')
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title(f'ROC Curve — KS={metrics["test_ks"]:.4f}', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[图] ROC曲线已保存: {save_path}")


def plot_score_distribution(params, woe_maps, bin_boundaries, df, save_path):
    """Score distribution on full dataset"""
    # Score the entire dataset
    scores = score_dataset(params, woe_maps, bin_boundaries, df)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(scores, bins=50, color='#3498db', alpha=0.7, edgecolor='white', linewidth=0.5)

    # Grade boundaries
    grade_colors = {'A': '#27ae60', 'B': '#2ecc71', 'C': '#f39c12', 'D': '#e67e22', 'E': '#e74c3c'}
    for grade, (lo, hi, desc, _) in RISK_GRADES.items():
        ax.axvline(x=lo, color=grade_colors.get(grade, 'gray'), linestyle='--', alpha=0.6, linewidth=1)
        ax.text(lo + 2, ax.get_ylim()[1] * 0.9, grade, fontsize=8, color=grade_colors.get(grade),
                fontweight='bold')

    ax.set_xlabel('Credit Score', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title(f'Score Distribution (n={len(scores):,})', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[图] 分数分布已保存: {save_path}")


def score_dataset(params, woe_maps, bin_boundaries, df):
    """Score all rows in a dataframe"""
    factor = params['factor']
    intercept = params['intercept']
    offset = params['offset']
    coefficients = params['coefficients']
    base_points = offset - factor * intercept

    scores = np.full(len(df), base_points)

    for feat in FINAL_FEATURES:
        col_woe = feat + '_woe'
        coef = coefficients.get(col_woe, 0)
        woe_map = woe_maps.get(feat, {})
        boundaries = bin_boundaries.get(feat)

        if boundaries is None or len(woe_map) == 0:
            continue

        raw_vals = df[feat].values
        for i, val in enumerate(raw_vals):
            if np.isnan(val):
                woe_val = 0.0
            else:
                # Find which bin this value belongs to
                bin_idx = np.digitize(val, boundaries[1:-1])  # exclude -inf and inf edges
                bin_label = f'Bin_{bin_idx}'
                woe_val = woe_map.get(bin_label, 0.0)

            scores[i] += -factor * coef * woe_val

    return np.clip(scores, 300, 850)


# ============================================================================
# Step 8: Report
# ============================================================================
def generate_phase4_report(params, metrics, bin_boundaries, woe_maps, output_dir):
    """Generate Phase 4 report"""
    report_path = os.path.join(output_dir, 'phase4_report.txt')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("  Phase 4: 评分卡模型构建 — 完整报告\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"训练时间: {TRAIN_DATE}\n")
        f.write(f"模型版本: v1.0\n\n")

        f.write("## 1. 评分卡参数\n\n")
        f.write(f"  Base Score:  {params['base_score']}\n")
        f.write(f"  PDO:         {params['pdo']}\n")
        f.write(f"  Base Odds:   {params['base_odds']}\n")
        f.write(f"  Factor:      {params['factor']:.4f}\n")
        f.write(f"  Offset:      {params['offset']:.4f}\n")
        f.write(f"  Intercept:   {params['intercept']:.6f}\n")
        f.write(f"  Base Points: {params['base_points']:.2f}\n\n")

        f.write("## 2. 模型性能\n\n")
        f.write(f"  Train AUC: {metrics['train_auc']:.4f}\n")
        f.write(f"  Test  AUC: {metrics['test_auc']:.4f}\n")
        f.write(f"  Train KS:  {metrics['train_ks']:.4f}\n")
        f.write(f"  Test  KS:  {metrics['test_ks']:.4f}\n")
        f.write(f"  Min KS required: {KS_MIN}\n\n")

        f.write("## 3. 特征系数\n\n")
        imp = sorted(metrics['feature_importance'], key=lambda x: x['coefficient'], reverse=True)
        for item in imp:
            f.write(f"  {item['feature']:<30} coef={item['raw_coef']:.6f}  |coef|={item['coefficient']:.4f}\n")

        f.write("\n## 4. 分箱详情\n\n")
        for feat in FINAL_FEATURES:
            boundaries = bin_boundaries.get(feat)
            woe_map = woe_maps.get(feat, {})
            f.write(f"  [{feat}]\n")
            if boundaries is not None:
                f.write(f"    Boundaries: {[round(b, 2) for b in boundaries[1:-1]]}\n")
            for bin_label, woe_val in sorted(woe_map.items()):
                f.write(f"    {bin_label}: WOE={woe_val:.4f}\n")
            f.write("\n")

        f.write("## 5. 风险等级\n\n")
        for grade, (lo, hi, desc, bad_rate) in RISK_GRADES.items():
            f.write(f"  {grade}: {lo}-{hi}  {desc}  Expected DR={bad_rate:.0%}\n")

        f.write("\n## 6. 面试要点\n\n")
        f.write("Q: 评分卡的分数怎么算出来的?\n")
        f.write("A: 逻辑回归输出log(odds) → 通过PDO/Base Score做线性变换\n")
        f.write("   600分基准，每20分odds翻倍。Factor=PDO/ln(2)≈28.85\n\n")
        f.write("Q: 为什么用逻辑回归而不是XGBoost?\n")
        f.write("A: 1)监管要求可解释性 2)WOE已线性化特征 3)评分卡转换需要系数\n")
        f.write("   4)监管报备时需要完整的评分卡表(每个bin几分)\n\n")
        f.write("Q: KS和AUC有什么区别?\n")
        f.write("A: AUC衡量整体排序能力，KS衡量最优区分点的区分度\n")
        f.write("   KS = max(|TPR - FPR|)，风控中KS>0.25基本可用\n")

    print(f"\n[报告] Phase 4 报告已生成: {report_path}")
    return report_path


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("=" * 80)
    print("    Phase 4: 评分卡模型构建")
    print("    逻辑回归 → 评分卡转换 → 序列化")
    print("=" * 80)

    # Step 1: Load data
    print("\n[步骤1/7] 加载建模数据...")
    df = load_modeling_data()

    # Step 2: Build WOE artifacts (bin boundaries + WOE maps)
    print(f"\n[步骤2/7] 构建分箱映射 & WOE编码...")
    bin_boundaries, woe_maps, iv_table = build_woe_artifacts(df, FINAL_FEATURES)

    # Step 3: Load WOE data and train LR
    print(f"\n[步骤3/7] 训练逻辑回归...")
    woe_csv = os.path.join(OUTPUT_DIR, 'modeling_data_woe.csv')
    lr_model, woe_cols, X_train, X_test, y_train, y_test = train_logistic_regression(woe_csv)

    # Step 4: Build scorecard
    print(f"\n[步骤4/7] 构建评分卡...")
    params = build_scorecard(lr_model, woe_cols)

    # Step 5: Evaluate
    print(f"\n[步骤5/7] 模型评估...")
    metrics = evaluate_model(lr_model, X_train, X_test, y_train, y_test, woe_cols)

    # Step 6: Generate scorecard table
    print(f"\n[步骤6/7] 生成评分卡表...")
    scorecard_table = generate_scorecard_table(params, woe_maps)
    with open(os.path.join(ARTIFACTS_DIR, 'scorecard_table.json'), 'w', encoding='utf-8') as f:
        json.dump(scorecard_table, f, indent=2, ensure_ascii=False)

    # Step 7: Serialize
    print(f"\n[步骤7/7] 序列化所有产出物...")
    serialize_artifacts(bin_boundaries, woe_maps, lr_model, params, metrics)

    # Visualization
    plot_roc_curve(metrics, os.path.join(OUTPUT_DIR, 'phase4_roc_curve.png'))
    plot_score_distribution(params, woe_maps, bin_boundaries, df,
                            os.path.join(OUTPUT_DIR, 'phase4_score_distribution.png'))

    # Report
    generate_phase4_report(params, metrics, bin_boundaries, woe_maps, OUTPUT_DIR)

    # Summary
    print(f"\n{'=' * 80}")
    print(f"  Phase 4 完成!")
    print(f"{'=' * 80}")
    print(f"  Test AUC:        {metrics['test_auc']:.4f}")
    print(f"  Test KS:         {metrics['test_ks']:.4f}")
    print(f"  Base Points:     {params['base_points']:.2f}")
    print(f"  Artifacts saved: {ARTIFACTS_DIR}")
    print(f"  入模特征:        {len(FINAL_FEATURES)} 个")
    print(f"\n  下一步: Phase 5 — FastAPI 评分接口")
    print(f"  运行: .\\venv\\Scripts\\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload")


if __name__ == "__main__":
    main()
