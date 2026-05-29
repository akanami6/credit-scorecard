"""
Generate Phase 3 operation manual PDF
Output: F:/claude/操作手册_Phase3_特征工程.pdf

Zero-basics step-by-step guide — can follow even without prior ML knowledge.
"""

from fpdf import FPDF
import os


class ManualPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.add_font('CN', '', 'C:/Windows/Fonts/simhei.ttf')
        self.add_font('CN', 'B', 'C:/Windows/Fonts/simhei.ttf')
        self.set_auto_page_break(True, 22)

    def cover(self, phase_num, title, subtitle):
        self.add_page()
        self.ln(25)
        self.set_font('CN', 'B', 26)
        self.set_text_color(25, 60, 120)
        self.cell(0, 14, f'Phase {phase_num} Operation Manual', new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(6)
        self.set_font('CN', 'B', 18)
        self.set_text_color(40, 90, 160)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(4)
        self.set_font('CN', '', 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, subtitle, new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(10)
        self.set_draw_color(40, 90, 160)
        self.set_line_width(0.6)
        y = self.get_y()
        self.line(40, y, 170, y)
        self.ln(10)
        self.set_font('CN', '', 10)
        self.set_text_color(130, 130, 130)
        self.cell(0, 7, 'Credit Scorecard Project | Mentor-guided | Zero-basics friendly', new_x="LMARGIN", new_y="NEXT", align='C')
        self.cell(0, 7, 'Every step explains WHY and HOW it is done in real companies', new_x="LMARGIN", new_y="NEXT", align='C')

    def h1(self, text):
        self.ln(5)
        self.set_font('CN', 'B', 15)
        self.set_text_color(25, 60, 120)
        self.set_fill_color(235, 242, 250)
        self.cell(0, 11, f'  {text}', new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def h2(self, text):
        self.ln(3)
        self.set_font('CN', 'B', 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font('CN', '', 10)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5.8, text, align='L')
        self.ln(1)

    def bullet(self, text, indent=6):
        self.set_font('CN', '', 10)
        self.set_text_color(60, 60, 60)
        left = self.l_margin + indent
        self.set_x(left)
        self.cell(4, 5.5, '-')
        self.set_x(left + 4)
        self.multi_cell(self.w - self.r_margin - left - 4, 5.5, text, align='L')

    def step_header(self, num, title):
        self.ln(2)
        self.set_font('CN', 'B', 12)
        self.set_text_color(180, 90, 30)
        self.set_fill_color(255, 248, 240)
        self.cell(0, 9, f'  Step {num}: {title}', new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(2)

    def code(self, text):
        self.ln(1)
        self.set_font('CN', '', 8.5)
        self.set_text_color(30, 30, 30)
        self.set_fill_color(248, 249, 250)
        lines = text.split('\n')
        for line in lines:
            self.cell(4, 4.5, '')
            self.cell(0, 4.5, line, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(60, 60, 60)

    def note(self, text):
        self.ln(1)
        self.set_font('CN', '', 9.5)
        self.set_text_color(40, 120, 80)
        self.set_fill_color(235, 250, 240)
        left = self.l_margin
        self.set_x(left)
        self.multi_cell(self.w - self.r_margin - left, 5.5, f'[Note] {text}', fill=True)
        self.ln(1)
        self.set_text_color(60, 60, 60)

    def warn(self, text):
        self.ln(1)
        self.set_font('CN', 'B', 9.5)
        self.set_text_color(180, 70, 30)
        self.set_fill_color(255, 245, 235)
        left = self.l_margin
        self.set_x(left)
        self.multi_cell(self.w - self.r_margin - left, 5.5, f'[Important] {text}', fill=True)
        self.ln(1)
        self.set_text_color(60, 60, 60)

    def check_item(self, text):
        self.set_font('CN', '', 10)
        self.set_text_color(60, 60, 60)
        left = self.l_margin
        self.set_x(left)
        self.cell(8, 6, '[ ]')
        self.set_x(left + 9)
        self.multi_cell(self.w - self.r_margin - left - 9, 6, text, align='L')

    def output_line(self, text):
        self.set_font('CN', '', 9)
        self.set_text_color(80, 80, 80)
        self.set_fill_color(245, 245, 245)
        left = self.l_margin
        self.set_x(left)
        self.multi_cell(self.w - self.r_margin - left, 4.8, text, fill=True, align='L')


def generate():
    pdf = ManualPDF()
    pdf.set_margin(20)

    pdf.cover(3, 'Feature Engineering & WOE/IV',
              'Estimated time: 1.5-2 hours | Output: IV ranking + WOE-encoded dataset')

    # ====== Prerequisites ======
    pdf.h1('Prerequisites')
    pdf.body('Before starting, confirm the following:')
    pdf.bullet('Phase 1 & Phase 2 completed, database file data/risk_db.sqlite exists')
    pdf.bullet('Virtual environment activated (terminal shows (venv) prefix)')
    pdf.bullet('Current directory: F:\\claude\\credit-scorecard\\')
    pdf.warn('If venv not activated: cd F:\\claude\\credit-scorecard then .\\venv\\Scripts\\Activate.ps1')

    # ====== Method 1: Quick Run ======
    pdf.h1('Method 1: Quick Run (5 minutes)')
    pdf.body('Run the full Phase 3 script with one command:')
    pdf.step_header(1, 'Execute Phase 3 script')
    pdf.code('python src\\phase3_feature_engineering.py')
    pdf.body('You will see: IV ranking table, feature selection process, WOE encoding output.')
    pdf.body('Then check the generated charts:')
    pdf.code('start data\\processed\\iv_ranking.png\nstart data\\processed\\woe_monotonic.png\nstart data\\processed\\correlation_heatmap.png')
    pdf.note('This quickly verifies everything works. For deep understanding, follow Method 2.')

    # ====== Method 2: Step by Step ======
    pdf.h1('Method 2: Step by Step in Python (Recommended for Learning)')
    pdf.body('Open Python interactively and execute each step to understand the logic.')

    pdf.step_header(2, 'Enter Python interactive environment')
    pdf.code('python')

    pdf.step_header(3, 'Load data')
    pdf.code(
        "import sys; sys.path.insert(0, '.')\n"
        "import sqlite3, pandas as pd, numpy as np\n"
        "from config import DB_PATH\n"
        '\n'
        "# Connect to database\n"
        "conn = sqlite3.connect(DB_PATH)\n"
        "df = pd.read_sql_query('''\n"
        "    SELECT a.loan_amnt, a.annual_inc, a.dti, a.fico_score,\n"
        "           a.credit_age, a.revol_util, a.inq_6m,\n"
        "           a.delinq_2yrs, a.pub_rec, l.loan_status\n"
        "    FROM apply_table a\n"
        "    LEFT JOIN loan_table l ON a.application_id = l.application_id\n"
        "    WHERE a.decision = 'Approved'\n"
        "''', conn)\n"
        "conn.close()\n"
        "\n"
        "# Create target variable\n"
        "df['target'] = (df['loan_status'] == 'Bad').astype(int)\n"
        "print(f'Samples: {len(df):,} | Bad rate: {df.target.mean():.2%}')"
    )
    pdf.output_line('Samples: 50,000 | Bad rate: 17.18%')

    # ====== Concept 1: Binning ======
    pdf.add_page()
    pdf.h1('Concept 1: Variable Binning')

    pdf.body('Binning divides a continuous variable into discrete intervals. For example, FICO score 580-850 can be divided into 5 bins: 580-640, 640-680, 680-720, 720-760, 760-850.')
    pdf.body('Why? Because the relationship between FICO and default risk may not be perfectly linear. Binning helps capture the true pattern.')

    pdf.step_header(4, 'Try equal-frequency binning on FICO score')
    pdf.code(
        "from src.phase3_feature_engineering import bin_equal_frequency\n"
        "\n"
        "# Equal-frequency: each bin gets ~same number of samples\n"
        "fico = df['fico_score']\n"
        "binned, boundaries = bin_equal_frequency(fico, df['target'], n_bins=5)\n"
        "print('Bin distribution:')\n"
        "print(binned.value_counts())\n"
        "print(f'\\nBin boundaries: {boundaries}')"
    )

    pdf.step_header(5, 'Try ChiMerge binning (industry standard)')
    pdf.code(
        "from src.phase3_feature_engineering import bin_chi_merge\n"
        "\n"
        "# ChiMerge: supervised binning — uses target to find best splits\n"
        "binned_chimerge, _ = bin_chi_merge(fico, df['target'], max_bins=6)\n"
        "print('ChiMerge bin distribution:')\n"
        "print(binned_chimerge.value_counts())"
    )
    pdf.note('ChiMerge is preferred in real scorecard projects because it uses the target variable (good/bad) to find optimal bin boundaries. Equal-frequency is blind to the target.')

    # ====== Concept 2: WOE ======
    pdf.add_page()
    pdf.h1('Concept 2: WOE Encoding')

    pdf.body('WOE = Weight of Evidence. It measures: "In this bin, are there more good or more bad customers compared to the overall sample?"')
    pdf.body('The formula is simple:')
    pdf.code(
        'WOE = ln(%Good in this bin / %Bad in this bin)\n'
        '\n'
        'WOE > 0  →  This bin has more good customers than average (low risk)\n'
        'WOE = 0  →  Average risk\n'
        'WOE < 0  →  This bin has more bad customers than average (high risk)'
    )

    pdf.step_header(6, 'Calculate WOE for FICO score')
    pdf.code(
        "from src.phase3_feature_engineering import calculate_woe_iv\n"
        "\n"
        "# Calculate WOE for each bin\n"
        "woe_df, iv, monotonic = calculate_woe_iv(binned_chimerge, df['target'])\n"
        "print('WOE per bin:')\n"
        "print(woe_df[['total', 'bad', 'woe']].round(4))\n"
        "print(f'\\nIV = {iv:.4f}')\n"
        "print(f'Monotonic = {monotonic}')"
    )
    pdf.body('Look at the WOE column: it should decrease steadily as FICO goes down (or increase as FICO goes up). This "steady change" is called monotonicity — a key quality check.')

    pdf.warn('Monotonicity matters: if WOE goes up-down-up across bins, it is harder to explain to regulators and less stable over time. Always check this before modeling.')

    # ====== Concept 3: IV ======
    pdf.add_page()
    pdf.h1('Concept 3: Information Value (IV)')

    pdf.body('IV measures a variable\'s overall ability to separate good from bad customers. Higher IV = better predictor.')
    pdf.body('The formula: IV = sum over all bins of (%Good - %Bad) * WOE')

    pdf.code(
        'IV Rating Scale:\n'
        '  < 0.02   Not Predictive   → Drop\n'
        '  0.02-0.1  Weak             → Consider dropping\n'
        '  0.1-0.3   Medium           → Include [OK]\n'
        '  0.3-0.5   Strong           → Key variable [OK][OK]\n'
        '  > 0.5     Suspicious       → Check for data leakage!'
    )

    pdf.step_header(7, 'Calculate IV for all numeric variables')
    pdf.code(
        "from src.phase3_feature_engineering import evaluate_all_variables\n"
        "\n"
        "features = ['loan_amnt', 'annual_inc', 'dti', 'fico_score',\n"
        "            'credit_age', 'revol_util', 'inq_6m',\n"
        "            'delinq_2yrs', 'pub_rec']\n"
        "\n"
        "iv_df, woe_maps = evaluate_all_variables(\n"
        "    df, features, target_col='target', bin_method='chimerge'\n"
        ")\n"
        "print(iv_df.to_string(index=False))"
    )
    pdf.body('Expected output: fico_score ranks #1 with IV=0.58, followed by inq_6m and dti. loan_amnt and pub_rec have near-zero IV.')

    # ====== Concept 4: Feature Selection ======
    pdf.add_page()
    pdf.h1('Concept 4: Feature Selection')

    pdf.body('We use a 3-step filter to select the final feature set:')

    pdf.h2('Step 1: IV Filter')
    pdf.code(
        "# Keep variables with IV >= 0.02\n"
        "passed_iv = iv_df[iv_df['iv'] >= 0.02]\n"
        "print(f'Passed IV filter: {len(passed_iv)} variables')"
    )

    pdf.h2('Step 2: Correlation Check')
    pdf.code(
        "# Check pairwise correlations among passed variables\n"
        "corr = df[list(passed_iv['variable'])].corr()\n"
        "print(corr.round(3))\n"
        "# If any pair > 0.7, drop the one with lower IV"
    )

    pdf.h2('Step 3: VIF Check')
    pdf.code(
        "from src.phase3_feature_engineering import check_vif\n"
        "\n"
        "vif_df = check_vif(df, list(passed_iv['variable']))\n"
        "print(vif_df)\n"
        "# FICO will have VIF=17 — but we protect it (IV=0.58!)"
    )

    pdf.warn('FICO has high VIF because other variables (credit_age, inq_6m, etc.) are components of FICO. In practice, we document this and keep FICO — dropping it would destroy the model.')

    # ====== Output ======
    pdf.add_page()
    pdf.h1('Output: Final Feature Set')

    pdf.body('After the 3-step filter, 7 features remain for Phase 4 modeling:')

    pdf.code(
        'Final Feature Set (7 variables):\n'
        '  1. fico_score      IV=0.5832  [Core credit score — strongest]\n'
        '  2. inq_6m          IV=0.1458  [Recent credit seeking behavior]\n'
        '  3. dti             IV=0.1410  [Debt-to-income — repayment pressure]\n'
        '  4. revol_util      IV=0.0985  [Revolving credit utilization]\n'
        '  5. delinq_2yrs     IV=0.0859  [Historical delinquency count]\n'
        '  6. credit_age      IV=0.0702  [Length of credit history]\n'
        '  7. annual_inc      IV=0.0546  [Annual income — repayment capacity]'
    )

    pdf.body('The WOE-encoded dataset is saved at:')
    pdf.output_line('data/processed/modeling_data_woe.csv — 50,000 rows x 10 columns')

    pdf.h2('Check the output')
    pdf.code(
        "# Exit Python first: exit()\n"
        "python -c \"import pandas as pd; df=pd.read_csv('data/processed/modeling_data_woe.csv'); print(df.head()); print(f'Shape: {df.shape}')\""
    )

    # ====== Key Charts ======
    pdf.h1('Key Charts Generated')
    pdf.bullet('IV Ranking chart: data/processed/iv_ranking.png — horizontal bar chart of IV values')
    pdf.bullet('WOE Monotonicity chart: data/processed/woe_monotonic.png — WOE trend per variable')
    pdf.bullet('Correlation Heatmap: data/processed/correlation_heatmap.png — feature correlations')
    pdf.bullet('Phase 3 Report: data/processed/phase3_report.txt — complete text report')

    pdf.step_header(8, 'View the charts')
    pdf.code(
        "start data\\processed\\iv_ranking.png\n"
        "start data\\processed\\woe_monotonic.png"
    )

    # ====== Knowledge Checklist ======
    pdf.add_page()
    pdf.h1('Knowledge Self-Check')
    pdf.body('After completing the above, try to answer these questions:')
    pdf.check_item('Why do we need binning before building a scorecard? (3 reasons)')
    pdf.check_item('What is the difference between equal-frequency, ChiMerge, and decision tree binning?')
    pdf.check_item('What is WOE? Write the formula. What does WOE > 0 mean?')
    pdf.check_item('What is IV? Write the formula. What does IV=0.15 mean?')
    pdf.check_item('Why is IV > 0.5 considered "suspicious"? Give an example.')
    pdf.check_item('What is WOE monotonicity? Why does it matter for scorecards?')
    pdf.check_item('What are the 3 steps of feature selection for scorecards?')
    pdf.check_item('Why keep FICO despite VIF=17? How do you explain this to a regulator?')
    pdf.check_item('What is the difference between correlation and VIF?')

    pdf.ln(5)
    pdf.h1('What You Accomplished')
    pdf.bullet('Applied ChiMerge supervised binning on 11 candidate features')
    pdf.bullet('Computed WOE (Weight of Evidence) encoding for all variables')
    pdf.bullet('Calculated IV (Information Value) and ranked variables by predictive power')
    pdf.bullet('Performed 3-step feature selection: IV → Correlation → VIF')
    pdf.bullet('Validated WOE monotonicity on all 7 retained features')
    pdf.bullet('Generated WOE-encoded dataset ready for Phase 4 logistic regression')
    pdf.bullet('Created 3 visualization charts for the analysis report')

    pdf.ln(3)
    pdf.warn('Resume-ready: "Performed ChiMerge supervised binning on 11 candidate features, computed WOE/IV for feature evaluation, implemented 3-stage feature selection pipeline, validated WOE monotonicity on 7 retained features. Identified FICO score as dominant predictor (IV=0.58)."')

    pdf.ln(5)
    pdf.set_font('CN', 'B', 12)
    pdf.set_text_color(40, 90, 160)
    pdf.cell(0, 8, 'Next: Phase 4 — Scorecard Model Building', new_x="LMARGIN", new_y="NEXT", align='C')

    # Save
    output = 'F:/claude/Phase3_Feature_Engineering_Manual.pdf'
    pdf.output(output)
    print(f'[OK] Phase 3 Manual: {output}')
    return output


if __name__ == '__main__':
    generate()
