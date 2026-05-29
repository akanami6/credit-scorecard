"""
Generate Phase 3 knowledge summary PDF
Output: F:/claude/Phase3_特征工程与WOE_IV.pdf

Phase 3 covers:
1. Variable Binning (ChiMerge, Equal Frequency, Decision Tree)
2. WOE (Weight of Evidence) encoding
3. IV (Information Value) calculation
4. Feature Selection (IV + Correlation + VIF)
5. Monotonicity check
"""

from fpdf import FPDF
import os


class ChinesePDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        font_path = 'C:/Windows/Fonts/simhei.ttf'
        self.add_font('CN', '', font_path)
        self.add_font('CN', 'B', font_path)
        self.set_auto_page_break(True, 25)

    def title_block(self, text):
        self.set_font('CN', 'B', 22)
        self.set_text_color(25, 60, 120)
        self.cell(0, 14, text, new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(4)

    def section_title(self, text):
        self.ln(4)
        self.set_font('CN', 'B', 14)
        self.set_text_color(40, 90, 160)
        self.set_fill_color(235, 242, 250)
        self.cell(0, 10, f'  {text}', new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def sub_title(self, text):
        self.set_font('CN', 'B', 11)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font('CN', '', 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6, text, align='L')
        self.ln(1)

    def bullet(self, text, indent=4):
        self.set_font('CN', '', 10)
        self.set_text_color(50, 50, 50)
        left = self.l_margin + indent
        self.set_x(left)
        self.cell(5, 6, '-')
        self.set_x(left + 5)
        self.multi_cell(self.w - self.r_margin - left - 5, 6, text, align='L')

    def code_block(self, text):
        self.ln(1)
        self.set_font('CN', '', 9)
        self.set_text_color(30, 30, 30)
        self.set_fill_color(246, 248, 250)
        lines = text.split('\n')
        for line in lines:
            self.cell(6, 5, '')
            self.cell(0, 5, line, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(50, 50, 50)

    def key_point(self, text):
        self.set_font('CN', '', 10)
        self.set_text_color(180, 70, 30)
        self.set_fill_color(255, 245, 235)
        self.set_x(self.l_margin)
        self.multi_cell(self.w - self.l_margin - self.r_margin, 6, f'[Key] {text}', fill=True)
        self.ln(1)
        self.set_text_color(50, 50, 50)

    def qa_block(self, q, a):
        self.set_font('CN', 'B', 10)
        self.set_text_color(160, 40, 40)
        self.cell(0, 6, f'[面试] {q}', new_x="LMARGIN", new_y="NEXT")
        self.set_font('CN', '', 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6, f'答: {a}')
        self.ln(2)

    def analysis_box(self, title, findings):
        self.set_font('CN', 'B', 10)
        self.set_text_color(40, 120, 80)
        self.set_fill_color(235, 250, 240)
        self.cell(0, 7, f'  [分析结果] {title}', fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font('CN', '', 10)
        self.set_text_color(50, 50, 50)
        for line in findings:
            self.bullet(line, indent=8)
        self.ln(2)

    def formula_block(self, formula, explanation):
        self.ln(1)
        self.set_font('CN', '', 10)
        self.set_text_color(40, 40, 40)
        self.set_fill_color(252, 252, 240)
        self.cell(10, 7, '')
        self.cell(0, 7, formula, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_font('CN', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(10, 5, '')
        self.cell(0, 5, explanation, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_text_color(50, 50, 50)


def generate():
    pdf = ChinesePDF()
    pdf.set_margin(20)

    # ====== Cover ======
    pdf.add_page()
    pdf.ln(30)
    pdf.title_block('Credit Scorecard Project')
    pdf.set_font('CN', 'B', 18)
    pdf.set_text_color(40, 90, 160)
    pdf.cell(0, 12, 'Phase 3: Feature Engineering & WOE/IV', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(15)

    pdf.set_draw_color(40, 90, 160)
    pdf.set_line_width(0.6)
    y = pdf.get_y()
    pdf.line(40, y, 170, y)
    pdf.ln(10)

    pdf.set_font('CN', '', 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, 'Variable Binning | WOE Encoding | IV Calculation | Feature Selection', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    pdf.cell(0, 8, '11 features evaluated, 7 selected for modeling, all WOE monotonic', new_x="LMARGIN", new_y="NEXT", align='C')

    # ====== Table of Contents ======
    pdf.add_page()
    pdf.section_title('Table of Contents')
    pdf.ln(3)
    toc = [
        '1. Why Feature Engineering Matters in Credit Scoring',
        '2. Variable Binning -- ChiMerge, Equal Frequency, Decision Tree',
        '3. WOE -- Weight of Evidence Encoding',
        '4. IV -- Information Value Calculation',
        '5. Monotonicity & Why It Matters',
        '6. Feature Selection: IV + Correlation + VIF',
        '7. Phase 3 Results -- IV Ranking & Final Feature Set',
        '8. Interview Q&A',
        '9. Resume Points',
    ]
    for item in toc:
        pdf.bullet(item, indent=6)
    pdf.ln(4)
    pdf.body('This document covers all Phase 3 knowledge. Companion script: src/phase3_feature_engineering.py.')

    # ====== Chapter 1: Why Feature Engineering ======
    pdf.add_page()
    pdf.section_title('1. Why Feature Engineering Matters in Credit Scoring')

    pdf.body('In a real credit scorecard project, a modeler spends ~70% of time on feature engineering -- binning, WOE encoding, and IV screening. The remaining 30% goes to model training, validation, and deployment. This is because logistic regression, the industry-standard model for scorecards, requires linear relationships between features and the target. Raw variables often have non-linear risk patterns, so we need WOE encoding to "linearize" them.')

    pdf.sub_title('The Scorecard Modeling Pipeline')
    pdf.code_block(
        'Raw Data → Binning → WOE Encoding → IV Screening → LR Model → Score Scale\n'
        '  |_____________________Phase 3___________________|  |______Phase 4______|'
    )

    pdf.sub_title('Why Logistic Regression Instead of XGBoost?')
    pdf.bullet('Regulatory compliance: LR coefficients are directly interpretable')
    pdf.bullet('Stability: LR is less sensitive to economic cycles than tree models')
    pdf.bullet('WOE preprocessing already handles non-linearity')
    pdf.bullet('Outputs probability -- directly usable for risk pricing')
    pdf.bullet('Industry standard: every major bank uses LR-based scorecards')

    pdf.key_point('Interview tip: When asked "why logistic regression?", always lead with "regulatory compliance and interpretability" -- that is the real reason banks use LR. Machine learning models are harder to explain to regulators.')

    # ====== Chapter 2: Variable Binning ======
    pdf.add_page()
    pdf.section_title('2. Variable Binning (Fen Xiang)')

    pdf.body('Binning divides a continuous variable into discrete intervals (bins). This is the first and most critical step in scorecard development. Bad binning leads to bad WOE, which leads to a bad model -- garbage in, garbage out.')

    pdf.sub_title('Why Binning?')
    pdf.bullet('Handles non-linear risk relationships (e.g., age-risk is U-shaped)')
    pdf.bullet('Reduces impact of outliers -- extreme values go into the edge bin')
    pdf.bullet('Improves model stability -- small data changes do not change bin boundaries')
    pdf.bullet('Business interpretability: "Age 20-25 high risk" vs "per year -0.003 risk"')
    pdf.bullet('Handles missing values naturally -- put them in their own bin')

    pdf.sub_title('Three Binning Methods')
    pdf.set_font('CN', 'B', 10)
    pdf.set_text_color(40, 120, 80)
    pdf.cell(0, 7, 'Method 1: Equal Frequency Binning (Deng Pin Fen Xiang)', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('CN', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.bullet('Each bin has approximately the same number of samples')
    pdf.bullet('Simple and fast, good for initial exploration')
    pdf.bullet('Drawback: ignores business logic, may split similar-risk clients')
    pdf.code_block(
        '# Python implementation\n'
        "bins = pd.qcut(series, q=5, duplicates='drop', retbins=True)[1]"
    )

    pdf.set_font('CN', 'B', 10)
    pdf.set_text_color(40, 120, 80)
    pdf.cell(0, 7, 'Method 2: ChiMerge Binning (Ka Fang Fen Xiang) -- INDUSTRY STANDARD', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('CN', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.bullet('Bottom-up merging: start with many fine bins, merge adjacent ones with lowest chi-square')
    pdf.bullet('Chi-square tests whether two adjacent bins have significantly different good/bad distributions')
    pdf.bullet('Low chi-square = similar risk = can be merged')
    pdf.bullet('This is THE most common method in real scorecard building')
    pdf.code_block(
        '# ChiMerge Algorithm:\n'
        '# 1. Start with max_bins*3 fine bins (equal frequency)\n'
        '# 2. For each adjacent pair, compute chi-square statistic\n'
        '# 3. Merge the pair with the SMALLEST chi-square\n'
        '# 4. Repeat until desired number of bins reached\n'
        '\n'
        '# Chi-square = sum((observed - expected)^2 / expected)\n'
        'from scipy.stats import chi2_contingency\n'
        'chi2, p, dof, expected = chi2_contingency(contingency_table)'
    )

    pdf.set_font('CN', 'B', 10)
    pdf.set_text_color(40, 120, 80)
    pdf.cell(0, 7, 'Method 3: Decision Tree Binning -- AUTOMATED', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('CN', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.bullet('Uses a single-variable decision tree to find optimal split points')
    pdf.bullet('Splits maximize information gain / Gini impurity reduction')
    pdf.bullet('More automated but more prone to overfitting')
    pdf.bullet('In practice: compare IV from ChiMerge vs Decision Tree, pick the higher one')

    pdf.key_point('Industry practice: ChiMerge is the default. If monotonicity fails, try manual adjustment or decision tree binning. Always validate binning with business sense -- does the pattern make sense?')

    # ====== Chapter 3: WOE ======
    pdf.add_page()
    pdf.section_title('3. WOE -- Weight of Evidence Encoding')

    pdf.body('WOE (Weight of Evidence) is the most important concept in credit scorecard development. It measures how much evidence each bin provides toward being a "good" or "bad" customer. WOE encoding is what makes logistic regression work for credit scoring.')

    pdf.sub_title('The WOE Formula')
    pdf.formula_block(
        'WOE_i = ln(%Good_i / %Bad_i)',
        'where %Good_i = Good count in bin i / Total Good count in sample'
    )
    pdf.formula_block(
        '     %Bad_i  = Bad count in bin i / Total Bad count in sample',
        ''
    )

    pdf.sub_title('Interpreting WOE Values')
    pdf.code_block(
        'WOE > 0  →  This bin has MORE good customers than average  →  Low risk\n'
        'WOE = 0  →  This bin is at the overall average              →  Neutral\n'
        'WOE < 0  →  This bin has MORE bad customers than average   →  High risk'
    )

    pdf.sub_title('Example: FICO Score WOE')
    pdf.code_block(
        'FICO Range      %Good    %Bad     WOE       Interpretation\n'
        '──────────────────────────────────────────────────────────\n'
        '580-640         5.2%    18.7%    -1.28     Strong bad signal\n'
        '640-680        12.4%    22.3%    -0.59     Moderate bad signal\n'
        '680-720        20.8%    20.1%    +0.03     Near average\n'
        '720-760        28.1%    19.8%    +0.35     Moderate good signal\n'
        '760-800        18.9%    11.2%    +0.52     Good signal\n'
        '800+           14.6%     7.9%    +0.61     Strong good signal'
    )

    pdf.sub_title('Why WOE Instead of Raw Values?')
    pdf.bullet('Linearization: converts U-shaped or non-monotonic patterns to linear')
    pdf.bullet('Missing value handling: "Missing" becomes a bin with its own WOE')
    pdf.bullet('Outlier robustness: extreme values go to edge bins, not raw values')
    pdf.bullet('Interpretability: "FICO 580-640 has WOE=-1.28" = clear risk signal')
    pdf.bullet('Standardization: all features on comparable WOE scale')

    pdf.key_point('This is the #1 interview question: "Why WOE encoding in scorecards?" Answer with these 5 points in order. The first point (linearization) is the most important -- logistic regression requires linearity.')

    # ====== Chapter 4: IV ======
    pdf.add_page()
    pdf.section_title('4. IV -- Information Value Calculation')

    pdf.body('IV (Information Value) measures the overall predictive power of a variable. It answers: "how well can this variable separate good from bad customers?" IV is the primary metric for feature selection in scorecard development.')

    pdf.sub_title('The IV Formula')
    pdf.formula_block(
        'IV = sum_over_bins ( %Good_i - %Bad_i ) * WOE_i',
        'IV is the weighted sum of WOE across all bins, weighted by the difference in proportions.'
    )

    pdf.sub_title('IV Rating Scale (Industry Standard)')
    pdf.code_block(
        'IV < 0.02       Not Predictive     → Drop from model\n'
        '0.02 <= IV < 0.1  Weak              → Marginal, consider dropping\n'
        '0.1 <= IV < 0.3   Medium            → GOOD, include in model\n'
        '0.3 <= IV < 0.5   Strong            → EXCELLENT, key variable\n'
        'IV >= 0.5         Suspicious         → Check for data leakage!'
    )

    pdf.sub_title('Why IV > 0.5 is "Suspicious"?')
    pdf.body('An IV above 0.5 is unusually high. It suggests the variable might contain future information (data leakage). For example, if "number of collection calls received" has IV=0.8 -- of course it predicts default, because only defaulting customers get collection calls! This variable would not be available at application time.')

    pdf.sub_title('Our Project IV Results')
    pdf.code_block(
        'Variable          IV       Rating\n'
        '──────────────────────────────────────\n'
        'fico_score        0.5832   Suspicious! (expected: it drives the synthetic data)\n'
        'inq_6m            0.1458   Medium\n'
        'dti               0.1410   Medium\n'
        'revol_util        0.0985   Weak\n'
        'delinq_2yrs       0.0859   Weak\n'
        'credit_age        0.0702   Weak\n'
        'annual_inc        0.0546   Weak\n'
        '--- IV=0.02 cutoff ---\n'
        'loan_to_income    0.0194   Not Pred. → Dropped\n'
        'payment_to_income 0.0194   Not Pred. → Dropped\n'
        'loan_amnt         0.0002   Not Pred. → Dropped\n'
        'pub_rec           0.0000   Not Pred. → Dropped (too sparse)'
    )

    pdf.key_point('Interview: "How do you select features for a scorecard?" Answer: "IV first (keep > 0.02), then correlation check (drop redundant pairs), then VIF (remove multicollinearity). Final check: WOE monotonicity and business sense."')

    # ====== Chapter 5: Monotonicity ======
    pdf.add_page()
    pdf.section_title('5. Monotonicity & Why It Matters')

    pdf.body('Monotonicity means WOE values should consistently increase or decrease across bins. In other words, as the variable value increases, the risk signal should move in ONE direction -- not up and down.')

    pdf.sub_title('Why Monotonicity Matters')
    pdf.bullet('Business interpretability: "Higher FICO = lower risk" is monotonic and intuitive')
    pdf.bullet('Regulatory acceptance: non-monotonic patterns raise questions')
    pdf.bullet('Model stability: monotonic relationships are more likely to hold in future data')
    pdf.bullet('Risk management: monotonic trends are easier to explain to non-technical stakeholders')

    pdf.sub_title('What If WOE Is Not Monotonic?')
    pdf.bullet('Try adjusting bin boundaries -- merge adjacent bins with similar WOE')
    pdf.bullet('Reduce the number of bins -- fewer bins = smoother trend')
    pdf.bullet('Consider the variable might have a genuine U-shaped risk pattern (e.g., age)')
    pdf.bullet('If truly non-monotonic: consider using dummy variables instead of WOE')
    pdf.bullet('Check for data quality issues in specific bins')

    pdf.sub_title('Our Project: All 7 Variables Monotonic')
    pdf.body('All 7 selected variables passed the monotonicity check. This is a good sign -- it means our binning was appropriate and the risk relationships are clean. In real projects, you often need several rounds of binning adjustment to achieve full monotonicity.')

    # ====== Chapter 6: Feature Selection ======
    pdf.add_page()
    pdf.section_title('6. Feature Selection: IV + Correlation + VIF')

    pdf.body('Feature selection in scorecard development follows a three-step filter process. Each step removes a different type of "bad" variable.')

    pdf.sub_title('Step 1: IV Filter')
    pdf.bullet('Keep variables with IV >= 0.02')
    pdf.bullet('Rationale: variables below 0.02 add noise, not signal')
    pdf.bullet('Our result: 7 passed, 4 dropped (loan_amnt, loan_to_income, payment_to_income, pub_rec)')

    pdf.sub_title('Step 2: Correlation Filter')
    pdf.bullet('If two variables have |correlation| > 0.7, keep only the one with higher IV')
    pdf.bullet('Rationale: collinear variables cause coefficient instability in LR')
    pdf.bullet('Our result: no pairs above 0.7 -- all 7 passed')

    pdf.sub_title('Step 3: VIF (Variance Inflation Factor)')
    pdf.formula_block(
        'VIF_i = 1 / (1 - R_i^2)',
        'where R_i^2 is the R-squared from regressing variable i on all other variables'
    )
    pdf.bullet('VIF = 1: completely independent')
    pdf.bullet('VIF 1-5: mild collinearity (acceptable)')
    pdf.bullet('VIF 5-10: moderate (needs monitoring)')
    pdf.bullet('VIF > 10: severe (usually dropped)')

    pdf.sub_title('The FICO Dilemma')
    pdf.body('In our project, FICO score had VIF=17.2 because it is correlated with credit_age, delinq_2yrs, inq_6m, and revol_util -- all of which are components that FICO itself synthesizes. We chose to KEEP FICO despite high VIF because:')
    pdf.bullet('IV=0.58 -- it is by far the strongest predictor')
    pdf.bullet('The collinearity with component variables is expected and explainable')
    pdf.bullet('In real practice, high-IV variables get "protected" status')
    pdf.bullet('Dropping FICO would cripple the model\'s predictive power')

    pdf.key_point('Interview: "What if a variable has high IV but high VIF?" Answer: "Protect high-IV variables (IV>0.15). FICO is the classic example -- it synthesizes many sub-components so it naturally correlates with them. Dropping FICO because of VIF would be throwing away the strongest signal. Instead, document the collinearity and explain it to regulators."')

    # ====== Chapter 7: Results ======
    pdf.add_page()
    pdf.section_title('7. Phase 3 Results Summary')

    pdf.sub_title('Input')
    pdf.bullet('11 numeric features (9 original + 2 derived)')
    pdf.bullet('50,000 samples, 17.18% bad rate')
    pdf.bullet('Binning method: ChiMerge (industry standard)')

    pdf.sub_title('Intermediate')
    pdf.bullet('IV computed for all 11 variables')
    pdf.bullet('WOE encoding applied, all 7 retained variables monotonic')
    pdf.bullet('Correlation heatmap generated -- no high-correlation pairs')
    pdf.bullet('VIF checked -- FICO high (17.2) but protected due to IV strength')

    pdf.sub_title('Output')
    pdf.bullet('7 features selected for Phase 4 modeling')
    pdf.bullet('WOE-encoded dataset saved: data/processed/modeling_data_woe.csv')
    pdf.bullet('Charts: IV ranking, WOE monotonicity, correlation heatmap')
    pdf.bullet('Report: data/processed/phase3_report.txt')

    pdf.sub_title('Final Feature Set')
    pdf.code_block(
        '#  Weight  Feature         IV       Role\n'
        '─────────────────────────────────────────────────────\n'
        '1  ★★★    fico_score      0.5832   Core risk score\n'
        '2  ★★     inq_6m          0.1458   Recent credit seeking\n'
        '3  ★★     dti             0.1410   Debt burden\n'
        '4  ★      revol_util      0.0985   Credit utilization\n'
        '5  ★      delinq_2yrs     0.0859   Historical delinquency\n'
        '6  ★      credit_age      0.0702   Credit history length\n'
        '7  ★      annual_inc      0.0546   Repayment capacity'
    )

    # ====== Chapter 8: Interview Q&A ======
    pdf.add_page()
    pdf.section_title('8. Interview Q&A')

    pdf.qa_block(
        'What is WOE? Why use WOE in scorecards?',
        'WOE = Weight of Evidence = ln(%Good/%Bad) per bin. We use it because: 1) It linearizes non-linear risk relationships for logistic regression; 2) It handles missing values naturally (Missing becomes its own bin); 3) It is robust to outliers; 4) It is interpretable -- WOE values directly map to risk; 5) It standardizes features onto a comparable scale. This is the #1 scorecard interview question.'
    )

    pdf.qa_block(
        'What is IV? How do you interpret IV values?',
        'IV = Information Value = sum of (%Good_i - %Bad_i) * WOE_i across all bins. It measures a variable\'s overall ability to separate good from bad. Scale: <0.02 not predictive, 0.02-0.1 weak, 0.1-0.3 medium (good for modeling), 0.3-0.5 strong, >0.5 suspicious (check for data leakage).'
    )

    pdf.qa_block(
        'What binning methods do you know? Which is best for scorecards?',
        'Three main methods: 1) Equal Frequency -- simple, good for initial exploration; 2) ChiMerge -- industry standard, bottom-up merging based on chi-square test of good/bad distribution similarity; 3) Decision Tree -- automated, uses information gain to find split points. ChiMerge is preferred because it is supervised (uses target), produces stable bins, and has strong statistical foundation. In practice, we try multiple methods and compare IV.'
    )

    pdf.qa_block(
        'What if WOE is not monotonic?',
        '1) First, try adjusting bin boundaries -- merge adjacent bins with similar WOE values; 2) Reduce the number of bins -- fewer bins produce smoother trends; 3) Check if the variable genuinely has a U-shaped risk pattern (e.g., age: young and old both higher risk); 4) If truly non-monotonic, consider converting to dummy variables instead of WOE encoding; 5) Always verify the business logic -- sometimes non-monotonicity reveals a data quality issue.'
    )

    pdf.qa_block(
        'How do you select features for a scorecard?',
        'Three-step filter: Step 1 (IV): keep variables with IV >= 0.02; Step 2 (Correlation): for pairs with |r| > 0.7, keep the one with higher IV; Step 3 (VIF): remove variables with VIF > 10, EXCEPT when a variable has very high IV (>0.15) -- in that case, document the collinearity and keep it. Final check: all retained variables must be WOE-monotonic and make business sense.'
    )

    pdf.qa_block(
        'Correlation vs VIF -- what is the difference?',
        'Correlation measures pairwise linear relationship between two variables. VIF measures how well one variable is explained by ALL other variables combined. A variable can have low pairwise correlations but high VIF -- this is multicollinearity. Example: X1 = X2 + X3. X1 may have moderate correlation with X2 and X3 individually, but perfect linear relationship with their combination. Only VIF catches this.'
    )

    # ====== Chapter 9: Resume ======
    pdf.add_page()
    pdf.section_title('9. Resume Points')

    pdf.sub_title('Chinese Resume')
    pdf.code_block(
        'Credit Scorecard System -- Feature Engineering & WOE/IV\n'
        '\n'
        '- Evaluated 11 candidate features using ChiMerge binning, the industry-standard\n'
        '  supervised discretization method for credit scorecards\n'
        '- Computed WOE (Weight of Evidence) encoding and IV (Information Value) for all\n'
        '  variables, identifying FICO score (IV=0.58) as the dominant risk predictor\n'
        '- Implemented 3-step feature selection: IV filter (>0.02) → correlation check\n'
        '  (<0.7) → VIF screening (<10), protecting high-IV variables from blind removal\n'
        '- Validated WOE monotonicity across all 7 retained features, ensuring regulatory-\n'
        '  grade model interpretability and stability\n'
        '- Delivered WOE-encoded modeling dataset (50K samples, 7 features) ready for\n'
        '  logistic regression modeling in Phase 4'
    )

    pdf.sub_title('English Resume')
    pdf.code_block(
        'Credit Scorecard System -- Feature Engineering & WOE/IV\n'
        '\n'
        '- Performed ChiMerge supervised binning on 11 candidate features, the\n'
        '  financial industry standard for credit scorecard discretization\n'
        '- Calculated WOE (Weight of Evidence) encoding and IV (Information Value)\n'
        '  for all variables; identified FICO score as the dominant predictor (IV=0.58)\n'
        '- Applied 3-stage feature selection pipeline: IV filtering (>0.02), correlation\n'
        '  screening (<0.7), and VIF analysis (<10) with high-IV protection rules\n'
        '- Ensured regulatory compliance through WOE monotonicity validation across\n'
        '  all 7 retained features, achieving full monotonicity\n'
        '- Produced WOE-transformed modeling dataset (50K records, 7 features) with\n'
        '  complete documentation for downstream logistic regression modeling'
    )

    pdf.sub_title('Interview Self-Introduction')
    pdf.body('"In the feature engineering phase, I applied ChiMerge -- the industry-standard supervised binning method -- to discretize 11 candidate variables. I then computed WOE encoding for each bin and IV for each variable. The IV ranking showed FICO score as the strongest predictor at 0.58, followed by recent inquiries and DTI. I implemented a three-stage feature selection pipeline -- IV filter, correlation check, and VIF screening -- protecting FICO from blind VIF removal because its high collinearity with sub-components is expected and explainable. All 7 retained features passed WOE monotonicity validation, ensuring the model is both predictive and regulator-friendly."')

    # ====== End Page ======
    pdf.add_page()
    pdf.ln(20)
    pdf.title_block('Phase 3 Complete')
    pdf.ln(10)
    pdf.set_font('CN', '', 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, 'Next: Phase 4 -- Scorecard Model Building', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 8, 'Logistic Regression / KS & AUC / Score Scale / Scorecard Table', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(15)

    pdf.set_font('CN', '', 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 6, 'Tech Stack: Python 3.13 | pandas | scipy | statsmodels | scikit-learn', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 6, 'Project Path: F:\\claude\\credit-scorecard\\', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 6, 'Script: src/phase3_feature_engineering.py', new_x="LMARGIN", new_y="NEXT", align='C')

    # Save
    output_path = 'F:/claude/Phase3_Feature_Engineering_WOE_IV.pdf'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    print(f'[OK] PDF generated: {output_path}')
    return output_path


if __name__ == '__main__':
    generate()
