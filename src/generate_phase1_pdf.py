"""
生成 Phase 1 知识总结 PDF
输出: F:/claude/Phase1_风控数据基础.pdf
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
        self.cell(4, 6, '')
        self.multi_cell(0, 6, f'[关键] {text}', fill=True)
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


def generate():
    pdf = ChinesePDF()
    pdf.set_margin(20)

    # ====== 封面 ======
    pdf.add_page()
    pdf.ln(30)
    pdf.title_block('信用评分卡项目')
    pdf.set_font('CN', 'B', 18)
    pdf.set_text_color(40, 90, 160)
    pdf.cell(0, 12, 'Phase 1: 风控数据基础', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(15)

    # 分隔线
    pdf.set_draw_color(40, 90, 160)
    pdf.set_line_width(0.6)
    y = pdf.get_y()
    pdf.line(40, y, 170, y)
    pdf.ln(10)

    pdf.set_font('CN', '', 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, '项目定位: 互联网消费金融 / 银行零售信贷审批', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 8, '行业对标: 蚂蚁 / 微众 / 招联 / 各大银行信用卡中心', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 8, '技术栈: Python + SQLite + sklearn + FastAPI + Streamlit', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    pdf.cell(0, 8, '导师制教学模式 | 每一步对应真实工作场景 | 附带面试解析', new_x="LMARGIN", new_y="NEXT", align='C')

    # ====== 目录 ======
    pdf.add_page()
    pdf.section_title('目录')
    pdf.ln(3)
    toc = [
        '1. 风控数据仓库架构 —— 三张核心表',
        '2. 时间窗口概念 —— 观察期 vs 表现期',
        '3. 好坏客户定义 —— M3+标准',
        '4. 核心SQL查询 —— 日常分析必备',
        '5. 数据字典 —— 关键变量释义',
        '6. 面试高频问答',
        '7. 简历成果提炼',
    ]
    for item in toc:
        pdf.bullet(item, indent=6)
    pdf.ln(4)
    pdf.body('本文档覆盖 Phase 1 全部知识点，可作为面试复习资料。建议配合 Jupyter Notebook (01_data_overview.ipynb) 动手实操。')

    # ====== 第1章: 风控数仓三张核心表 ======
    pdf.add_page()
    pdf.section_title('1. 风控数据仓库架构 —— 三张核心表')

    pdf.body('在银行和互联网金融公司，风控数据仓库以这三张表为核心组成星型模型。这是风控分析师每天都要打交道的底层数据结构。')

    pdf.sub_title('ER 关系图')
    pdf.code_block(
        '申请时                    放款后                       还款中\n'
        'apply_table ──────────> loan_table ───────────> repayment_table\n'
        ' (申请表)      审批通过     (借据表)      每期还款     (还款表)\n'
        ' 1人可多笔               1笔申请=1笔借据             1笔借据=N期还款'
    )

    pdf.sub_title('表1: apply_table (申请表)')
    pdf.body('存储借款人提交申请时的"快照"信息。关键特征：同一借款人多次申请会有多条记录。为什么必须用快照而不用实时数据？因为审批决策必须基于申请时刻的信息，事后变化不能用来回溯评估——否则就是"数据穿越"。')
    pdf.code_block(
        '核心字段:\n'
        '  application_id   PRIMARY KEY    申请ID\n'
        '  member_id                       借款人ID\n'
        '  apply_date                      申请日期\n'
        '  loan_amnt                       申请金额\n'
        '  term                            申请期限(月)\n'
        '  purpose                         借款目的\n'
        '  annual_inc                      年收入\n'
        '  dti                             负债收入比(Debt-to-Income)\n'
        '  fico_score                      FICO信用分\n'
        '  credit_age                      信用历史长度(年)\n'
        '  revol_util                      循环额度利用率\n'
        '  inq_6m                          近6月征信查询次数\n'
        '  delinq_2yrs                     近2年逾期次数\n'
        '  home_ownership                  房屋状态\n'
        '  emp_length                      工作年限\n'
        '  decision                        审批结果'
    )

    pdf.sub_title('表2: loan_table (借据表)')
    pdf.body('审批通过后生成借据，只关注最终放款的订单。一笔申请(application)对应一笔借据(loan)，但一个借款人(member)可以有多笔借据。这张表记录放款后的实际信息——实际利率、剩余本金、当前还款状态。')
    pdf.code_block(
        '核心字段:\n'
        '  loan_id           PRIMARY KEY    借据ID\n'
        '  application_id    FK             关联申请ID\n'
        '  member_id         FK             借款人ID\n'
        '  issue_date                       放款日期\n'
        '  loan_amnt                        实际放款金额\n'
        '  term                             期限(月)\n'
        '  int_rate                         利率\n'
        '  installment                      月还款额\n'
        '  grade                            风险等级(A/B/C/D/E)\n'
        '  fico_score                       放款时FICO分\n'
        '  loan_status                      当前状态(Good/Bad)\n'
        '  total_pymnt                      累计还款额\n'
        '  outstanding_principal            剩余本金'
    )

    pdf.sub_title('表3: repayment_table (还款表)')
    pdf.body('每笔借据的每期还款明细。一笔借据产生N期还款记录(如12期=12条)。通过这张表可以计算：逾期天数(DPD)、累计还款额、提前还款行为。DPD = Days Past Due，即实际还款日与计划还款日的差值。')
    pdf.code_block(
        '核心字段:\n'
        '  repayment_id    PRIMARY KEY    还款记录ID\n'
        '  loan_id         FK             关联借据ID\n'
        '  schedule_date                  计划还款日\n'
        '  actual_date                    实际还款日\n'
        '  schedule_amt                   计划还款金额\n'
        '  actual_amt                     实际还款金额\n'
        '  dpd                            逾期天数(Days Past Due)\n'
        '  status                         还款状态'
    )

    pdf.key_point('面试技巧: 被问到"风控数据库怎么设计"时，画出这三张表的ER关系图就是满分答案。三张表的核心逻辑：申请表存快照、借据表存合同、还款表存明细。')

    # ====== 第2章: 时间窗口 ======
    pdf.add_page()
    pdf.section_title('2. 时间窗口概念 —— 观察期 vs 表现期')

    pdf.body('时间窗口是风控建模最基础也最重要的概念。如果搞错时间窗口，就会产生"数据穿越"(Data Leakage)——用未来的信息预测过去，这是风控建模中最严重的错误，一旦发现，模型必须报废重做。')

    pdf.code_block(
        '时间轴 ─────────────────────────────────────────────>\n'
        '\n'
        '  |<──── 观察期(24个月) ────>|<──── 表现期(12个月) ────>|\n'
        '  |                           |                           |\n'
        '  观察点                      放款日                     表现点\n'
        ' (取历史特征)               (申请/放款)                (看是否逾期)\n'
        '\n'
        '示例:\n'
        '  放款日: 2018-06-15\n'
        '  观察期: 2016-06-15 ~ 2018-06-15  (借款前2年的历史行为)\n'
        '  表现期: 2018-06-15 ~ 2019-06-15  (放款后1年的还款表现)\n'
        '  判断: 如果2019-06-15时逾期>=90天 -> 坏客户'
    )

    pdf.sub_title('观察期 (Observation Window)')
    pdf.body('看借款人历史行为的窗口，通常是借款前12-24个月。在这段时间内提取：近6个月查询次数、近2年逾期次数、当前FICO分数、收入、负债比等。原则：只能用在放款日之前已经存在的信息。')

    pdf.sub_title('表现期 (Performance Window)')
    pdf.body('看借款后还款表现的窗口，通常是放款后6-12个月。在这段时间内观察：是否逾期、逾期多久、是否还清。表现期太短(如3个月)则很多坏客户还没暴露，太长(如2年)则可用样本量大幅减少。12个月是行业标准做法。')

    pdf.key_point('核心原则: 特征(X)必须在标签(Y)的时间之前产生。违反了这条就叫数据穿越。面试中只要你提到"数据穿越"这个概念并准确解释，面试官对你的评价立刻提升一个档次。')

    # ====== 第3章: 好坏客户定义 ======
    pdf.section_title('3. 好坏客户定义 —— M3+ 标准')

    pdf.body('构建评分卡模型之前，必须先定义"什么是好客户、什么是坏客户"。这个定义直接决定了模型的预测目标，是整个项目的起点。')

    pdf.sub_title('行业标准定义')
    pdf.code_block(
        '坏客户 (Bad):\n'
        '  在表现期内，逾期天数(DPD) >= 90天 (即 M3+)\n'
        '  这是行业黄金标准，国内外银行通用\n'
        '\n'
        '好客户 (Good):\n'
        '  在表现期内，逾期天数(DPD) < 30天\n'
        '  且没有违约记录\n'
        '\n'
        '中间客户 (Indeterminate):\n'
        '  逾期30-89天 (M1-M2)\n'
        '  这些客户的好壞不明显，会被剔除出建模样本\n'
        '  原因: 保留他们会增加模型噪声，降低区分能力'
    )

    pdf.sub_title('为什么是M3+(90天)而不是M1+(30天)？')
    pdf.body('M1逾期(30天)可能是忘记还款、出差、银行系统延迟等非主观原因；M3+逾期(90天)则基本可以确定是还款意愿或还款能力出了问题。从银行的角度，M3+是计提坏账准备的监管标准线，具有监管合规意义。')

    pdf.sub_title('逾期阶段说明')
    pdf.code_block(
        'M0: DPD = 0       正常还款\n'
        'M1: DPD = 1-30天   轻度逾期(可能忘记)\n'
        'M2: DPD = 31-60天  中度逾期(需要催收介入)\n'
        'M3: DPD = 61-90天  重度逾期(计提拨备)\n'
        'M4+: DPD > 90天    严重逾期(核销/write-off)'
    )

    # ====== 第4章: 核心SQL查询 ======
    pdf.add_page()
    pdf.section_title('4. 核心SQL查询 —— 日常分析必备')

    pdf.body('风控分析师每天大量时间在写SQL。以下是最常用的查询模式，理解这些SQL就掌握了从数据库中提取风险信息的基本能力。')

    pdf.sub_title('查询1: 整体资产质量概览')
    pdf.body('这是任何风控分析的第一步：先看整体逾期率和坏账率，了解资产质量的基准线。如果一看坏账率20%，那任何模型都救不了——先检查数据质量。')
    pdf.code_block(
        'SELECT \n'
        '    loan_status,\n'
        '    COUNT(*) as cnt,\n'
        '    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct,\n'
        '    ROUND(AVG(loan_amnt), 0) as avg_loan_amnt,\n'
        '    ROUND(AVG(int_rate), 2) as avg_int_rate,\n'
        '    ROUND(AVG(fico_score), 0) as avg_fico\n'
        'FROM loan_table\n'
        'GROUP BY loan_status;'
    )

    pdf.sub_title('查询2: 分维度坏账率分析')
    pdf.body('按借款目的、FICO分段、收入分段等维度分别计算坏账率——这是"风险画像"的核心。面试官常问："你拿到一个借贷数据集，先分析什么？"——就是从这些维度拆解开始。')
    pdf.code_block(
        '-- 按借款目的分析坏账率\n'
        'SELECT \n'
        '    a.purpose,\n'
        '    COUNT(*) as total,\n'
        '    SUM(CASE WHEN l.loan_status = \'Bad\' THEN 1 ELSE 0 END) as bad_cnt,\n'
        '    ROUND(bad_cnt * 100.0 / total, 2) as bad_rate\n'
        'FROM loan_table l\n'
        'JOIN apply_table a ON l.application_id = a.application_id\n'
        'GROUP BY a.purpose\n'
        'ORDER BY bad_rate DESC;'
    )

    pdf.sub_title('查询3: FICO分段风险分析')
    pdf.body('FICO分是信用评估领域最重要的单一指标。模型开发中，通常按FICO分段后使用CASE WHEN做分箱。好的分箱需要保证每个箱体内样本量足够且坏账率单调。')
    pdf.code_block(
        'SELECT \n'
        '    CASE \n'
        '        WHEN fico < 620 THEN \'<620\'\n'
        '        WHEN fico < 660 THEN \'620-660\'\n'
        '        WHEN fico < 700 THEN \'660-700\'\n'
        '        ELSE \'700+\' END as fico_band,\n'
        '    COUNT(*) as cnt,\n'
        '    ROUND(AVG(CASE WHEN loan_status=\'Bad\' THEN 1 ELSE 0 END),3) as bad_rate\n'
        'FROM loan_table GROUP BY fico_band ORDER BY MIN(fico_score);'
    )

    pdf.key_point('SQL是风控分析师最重要的硬技能。面试中经常直接让你手写SQL。建议把上面这几条SQL自己敲一遍，理解每个CASE WHEN和聚合函数的含义。')

    # ====== 第5章: 数据字典 ======
    pdf.add_page()
    pdf.section_title('5. 数据字典 —— 关键变量释义')

    pdf.body('理解每个变量的业务含义是做特征工程的前提。以下列出本项目中最关键的变量，按类别分组：')

    pdf.sub_title('借贷信息')
    pdf.bullet('loan_amnt (借款金额): 客户申请/实际获得的贷款金额，范围通常1000-40000')
    pdf.bullet('term (借款期限): 36个月或60个月，短期限风险通常更高(因月供更高)')
    pdf.bullet('int_rate (利率): 风险定价的结果，高风险客户利率更高')
    pdf.bullet('purpose (借款目的): debt_consolidation(债务重组)最常见')

    pdf.sub_title('信用评估')
    pdf.bullet('fico_score (FICO信用分): 美国最通用的个人信用评分，范围300-850，越高越好。综合还款历史(35%)、负债水平(30%)、信用长度(15%)、新信用(10%)、信用类型(10%)五大维度')
    pdf.bullet('credit_age_years (信用历史长度): 从第一笔信用记录到现在的年数，越长越好')
    pdf.bullet('revol_util (循环额度利用率): 已用信用卡额度/总额度，高利用率=风险信号')
    pdf.bullet('inq_6m (近6月查询次数): 申请新信用时产生的硬查询(hard pull)次数，查询多说明在大量借钱')
    pdf.bullet('delinq_2yrs (近2年逾期次数): 过去2年内逾期30天以上的次数')
    pdf.bullet('pub_rec (公开违约记录): 破产、判决留置等负面记录数')

    pdf.sub_title('还款能力')
    pdf.bullet('annual_inc (年收入): 借款人自报的年收入，越高还款能力越强')
    pdf.bullet('dti (Debt-to-Income): 每月债务还款额/月收入，衡量还款压力。监管通常要求<43%')
    pdf.bullet('emp_length (工作年限): 工作稳定性指标，10年以上为最佳')

    pdf.sub_title('其他信息')
    pdf.bullet('home_ownership (房屋状态): MORTGAGE(有房贷) / RENT(租房) / OWN(自有)')
    pdf.bullet('addr_state (所在州): 不同地区的经济状况不同，加州/纽约/德州是最大市场')

    # ====== 第6章: 面试高频问答 ======
    pdf.add_page()
    pdf.section_title('6. 面试高频问答')

    pdf.qa_block(
        '风控数据仓库有哪些核心表？分别记录什么信息？',
        '三张表。申请表(apply_table)记录申请时刻的快照数据；借据表(loan_table)记录放款后的合同和还款状态；还款表(repayment_table)记录每期还款明细。三张表通过application_id和loan_id关联。核心设计理念：申请表1:N借据表1:N还款表。'
    )

    pdf.qa_block(
        '什么是观察期和表现期？为什么需要这两个窗口？',
        '观察期是借款前取历史特征的窗口(通常24个月)，表现期是借款后看还款表现的窗口(通常12个月)。核心目的是防止数据穿越——建模时只能用放款前已有的信息来预测未来的还款表现。如果没有时间窗口约束，可能会把逾期后的数据当成特征来预测逾期，模型看似很准但完全不可用。'
    )

    pdf.qa_block(
        '怎么定义"坏客户"？为什么选M3+而不是M1+？',
        '表现期内逾期>=90天(M3+)定义为坏客户，逾期<30天定义为好客户，M1-M2被剔除。M3+是行业标准，原因：1) M1可能是忘记还款而非真正违约意图；2) M3+是银行计提坏账准备的监管标准线；3) M1-M2客户的好坏不明确，纳入建模会增加噪声。注意要说明中间客户的处理方式，这是加分点。'
    )

    pdf.qa_block(
        '什么是数据穿越(Data Leakage)？举例说明。',
        '数据穿越是指模型训练时使用了在预测时点还不可知的信息。典型案例：用"放款后第3个月的还款行为"来预测"借款人是否会违约"——但放款后的还款行为在审批时根本不知道。另一个常见例子：用"贷后回访收入"替代"申请时自报收入"，前者是贷后才知道的。'
    )

    pdf.qa_block(
        'FICO分是什么？为什么它是风控最重要的单一指标？',
        'FICO是美国Fair Isaac公司开发的个人信用评分，范围300-850。它综合了5大维度：还款历史(35%)、负债水平(30%)、信用历史长度(15%)、新信用(10%)、信用类型(10%)。它是风控最重要的单一指标因为：1)它是经过数十年数据验证的标准化指标；2)天然具有良好的风险排序能力；3)可解释性强，监管接受度高。在中国对应的是央行征信分和百行征信分。'
    )

    pdf.qa_block(
        'SQL中如何计算各维度的坏账率？',
        '基本模式：先按维度用GROUP BY分组，然后用CASE WHEN + SUM + COUNT计算每组内的坏客户占比。关键是理解聚合函数和CASE WHEN的组合使用。风控SQL最常用的就是这种分组统计模式。面试时如果让你现场写一条分析SQL，大概率就是这种模式。'
    )

    # ====== 第7章: 简历成果 ======
    pdf.add_page()
    pdf.section_title('7. 简历成果提炼')

    pdf.body('完成 Phase 1 后，你可以在简历中这样写（中英文两个版本，适用于不同场景）：')

    pdf.sub_title('中文版（简历项目经验栏）')
    pdf.code_block(
        '信用评分卡系统开发 —— 数据基础与风险架构\n'
        '\n'
        '- 设计并搭建风控数据仓库模型，采用申请-借据-还款三层架构，\n'
        '  管理5万笔借贷申请及60万条还款记录\n'
        '- 基于SQL完成信贷资产风险画像分析，按借款目的/FICO分段/收入\n'
        '  维度拆解坏账率分布，识别高违约风险客群特征\n'
        '- 掌握观察期(24个月)/表现期(12个月)时间窗口划分方法，\n'
        '  严格按照M3+(DPD>=90)标准定义好坏客户标签\n'
        '- 建立完整的数据字典，覆盖借贷信息/信用评估/还款能力3大类\n'
        '  15+个核心变量'
    )

    pdf.sub_title('英文版 (English Resume)')
    pdf.code_block(
        'Credit Scorecard System - Data Foundation & Risk Architecture\n'
        '\n'
        '- Designed a 3-tier risk data warehouse model (Application-Loan-Repayment)\n'
        '  managing 50K loan applications and 600K repayment records using SQLite\n'
        '- Conducted portfolio risk profiling via SQL, decomposing default rates by\n'
        '  purpose, FICO band, and income level to identify high-risk segments\n'
        '- Applied Observation Window (24M) / Performance Window (12M) methodology\n'
        '  with M3+ (DPD>=90) bad definition to prevent data leakage\n'
        '- Documented comprehensive data dictionary covering 15+ variables across\n'
        '  loan attributes, credit assessment, and repayment capacity categories'
    )

    pdf.sub_title('面试自我介绍中可以这样引入')
    pdf.body('"我最近在做一个完整的信用评分卡项目，从数据仓库搭建开始。在数据阶段，我设计了三张核心表——申请表、借据表、还款表，用观察期24个月/表现期12个月的时间窗口来划分建模样本，按M3+的标准定义坏客户标签。整个过程模拟了真实银行风控数仓的架构设计流程。"')

    pdf.key_point('简历技巧: 用数字说话(50K/600K/24M/12M/M3+)，展示你理解核心概念并能量化描述项目规模。面试官看到这些数字和术语，立刻知道你不是纸上谈兵。')

    # ====== 尾页 ======
    pdf.add_page()
    pdf.ln(20)
    pdf.title_block('Phase 1 完成')
    pdf.ln(10)
    pdf.set_font('CN', '', 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, '下一阶段: Phase 2 — EDA与风险画像', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 8, 'Vintage分析 / Roll Rate分析 / 单变量分析 / 缺失值处理', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(15)

    # 技术栈
    pdf.set_font('CN', '', 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 6, '项目技术栈: Python 3.13 | SQLite | pandas | matplotlib | scikit-learn | FastAPI | Streamlit', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 6, '项目路径: F:\\claude\\credit-scorecard\\', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 6, f'生成日期: Phase 1 完成日', new_x="LMARGIN", new_y="NEXT", align='C')

    # 保存
    output_path = 'F:/claude/Phase1_风控数据基础.pdf'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    print(f'[OK] PDF已生成: {output_path}')
    return output_path


if __name__ == '__main__':
    generate()
