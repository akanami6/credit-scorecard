"""
生成 Phase 2 知识总结 PDF
输出: F:/claude/Phase2_EDA与风险画像.pdf
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
        for line in text.split('\n'):
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


def generate():
    pdf = ChinesePDF()
    pdf.set_margin(20)

    # ====== 封面 ======
    pdf.add_page()
    pdf.ln(30)
    pdf.title_block('信用评分卡项目')
    pdf.set_font('CN', 'B', 18)
    pdf.set_text_color(40, 90, 160)
    pdf.cell(0, 12, 'Phase 2: EDA与风险画像', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(15)

    pdf.set_draw_color(40, 90, 160)
    pdf.set_line_width(0.6)
    y = pdf.get_y()
    pdf.line(40, y, 170, y)
    pdf.ln(10)

    pdf.set_font('CN', '', 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, 'Roll Rate Analysis | Vintage 分析 | 单变量分析 | 缺失值/异常值处理', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    pdf.cell(0, 8, '本阶段产出: 5大分析模块, 6个可视化图表, 4道面试问答', new_x="LMARGIN", new_y="NEXT", align='C')

    # ====== 目录 ======
    pdf.add_page()
    pdf.section_title('目录')
    pdf.ln(3)
    toc = [
        '1. Roll Rate Analysis -- 从数据验证好坏客户定义',
        '2. Vintage 分析 -- 风控最重要的资产质量评估工具',
        '3. 单变量分析 -- 每个变量与违约的关系',
        '4. 缺失值分析 -- 缺失本身也有信息量',
        '5. 异常值检测 -- 区分三类异常',
        '6. 相关性分析 -- 量化变量预测力',
        '7. 面试高频问答',
        '8. 简历成果提炼',
    ]
    for item in toc:
        pdf.bullet(item, indent=6)
    pdf.ln(4)
    pdf.body('本文档覆盖 Phase 2 全部知识点。建议配合 Jupyter Notebook (02_eda_risk_profile.ipynb) 动手实操，观察每一步的输出结果。')

    # ====== 第1章: Roll Rate Analysis ======
    pdf.add_page()
    pdf.section_title('1. Roll Rate Analysis -- 从数据验证好坏定义')

    pdf.body('Roll Rate(滚动率)是风控领域最核心的逾期分析方法之一。它衡量的是：当前处于某个逾期阶段的客户，在下一个账期"滚动"到更严重逾期阶段的概率。')

    pdf.sub_title('为什么需要Roll Rate？')
    pdf.bullet('好坏客户定义应该是数据驱动的，不是拍脑袋的')
    pdf.bullet('如果一个M1客户有80%概率在6个月内滚到M3+，那M1就是准坏客户')
    pdf.bullet('如果大部分M2客户最终会还清，那M3+才是真正的坏客户阈值')
    pdf.bullet('银行每季度更新Roll Rate报告，监控逾期迁移趋势')

    pdf.sub_title('Roll Rate 计算方法')
    pdf.code_block(
        '1. 对每笔借据按账龄(period)排列还款记录\n'
        '2. 每期DPD转为逾期阶段: M0(正常), M1(1-30天), M2(31-60天), \n'
        '   M3(61-90天), M4+(90天以上)\n'
        '3. 统计相邻两期的状态转移: Flow[当前状态][下期状态]\n'
        '4. 按行归一化得到迁移概率矩阵\n'
        '5. 对所有相邻月份对的矩阵取平均'
    )

    pdf.sub_title('解读Roll Rate矩阵')
    pdf.code_block(
        '            下一期\n'
        '            M0    M1    M2    M3   M4+\n'
        '当前  M0   0.95  0.03  0.01  0.01  0.00\n'
        '      M1   0.20  0.30  0.25  0.15  0.10\n'
        '      M2   0.05  0.05  0.15  0.40  0.35\n'
        '      M3   0.01  0.01  0.03  0.15  0.80\n'
        '      M4+  0.00  0.00  0.00  0.05  0.95'
    )

    pdf.body('读法: M0行M0列=0.95，表示95%的正常客户下个月仍然正常。M2行M3+M4+列=0.75，表示75%的M2客户会继续恶化到M3+。')

    pdf.key_point('面试黄金答案: "我们通过Roll Rate分析来确定坏客户定义。如果M2->M3+迁移率>60%，说明M2已经是事实上的坏客户，可以放宽定义；如果迁移率<30%，M3+才是合理的坏客户阈值。"')

    pdf.sub_title('本项目Roll Rate分析结果')
    pdf.body('基于50,000笔借据的12期还款数据，M0客户保持正常的比例为95.3%。这个数字意味着每月约4.7%的正常客户会进入逾期状态——这对于消费信贷来说是正常的迁徙率。一旦客户进入M3+阶段，回到M0的概率接近于0。')

    # ====== 第2章: Vintage Analysis ======
    pdf.add_page()
    pdf.section_title('2. Vintage 分析 -- 风控最重要的资产质量工具')

    pdf.body('Vintage分析是风控领域的"通用语言"。它按放款月份分组，追踪每个批次在不同账龄(MOB, Month-on-Book)的累计坏账率变化。银行业、消费金融、P2P——所有信贷机构都用Vintage图来评估资产质量。')

    pdf.sub_title('Vintage分析回答什么问题？')
    pdf.bullet('今年批的客户比去年的好还是差？（不同月份曲线对比）')
    pdf.bullet('坏账主要在放款后第几个月暴露？（曲线陡峭程度）')
    pdf.bullet('风控策略调整后，资产质量改善了吗？（曲线收敛还是发散）')
    pdf.bullet('当前资产组合的预期损失率是多少？（MOB12坏账率）')

    pdf.sub_title('Vintage 图解读方法（四步法）')
    pdf.bullet('第一步: 看趋势——曲线收敛说明风控策略稳定，发散说明策略在调整或客群在变化')
    pdf.bullet('第二步: 看陡峭程度——曲线越陡，坏账暴露越快，客群质量越差')
    pdf.bullet('第三步: 看MOB6——行业标准benchmark，大部分坏账在6个月内暴露')
    pdf.bullet('第四步: 看MOB12——作为最终损失率的估计，用于计提拨备')

    pdf.sub_title('面试标准回答')
    pdf.body('"拿到一张Vintage图，我先看三条：第一，曲线是收敛还是发散？收敛说明风控稳定。第二，最近几个月的Vintage有没有明显高于历史？如果有，需要立刻排查是不是策略出了问题或客群变了。第三，MOB12的坏账率是多少？这个数字直接用于拨备计算和风险定价。"')

    pdf.sub_title('本项目Vintage分析结果')
    pdf.body('分析覆盖24个放款月份(2018年1月至2019年12月)，MOB1-MOB12共计288个数据点。MOB12累计坏账率区间为3.47%-5.41%，各月曲线趋势收敛，说明风控策略在这个时间段相对稳定。')

    # ====== 第3章: 单变量分析 ======
    pdf.add_page()
    pdf.section_title('3. 单变量分析 -- 理解每个变量与违约的关系')

    pdf.body('在进入特征工程之前，需要逐一理解每个变量和违约之间的关系。这一步帮你判断哪些变量值得进入模型，以及变量的风险排序是否合理。')

    pdf.sub_title('分析方法')
    pdf.bullet('数值型变量: 等频分10箱, 画每个箱的坏账率折线图, 观察单调性')
    pdf.bullet('类别型变量: 计算每个类别的坏账率, 画水平柱状图对比')
    pdf.bullet('箱线图: Good vs Bad 的分布对比, 看两个箱体的重叠程度')
    pdf.bullet('重叠越少 -> 区分度越好; 中位数差距越大 -> 预测力越强')

    pdf.sub_title('本项目关键发现')
    pdf.analysis_box('FICO信用分 (最强单一预测变量)', [
        '坏账率从最低分段的34.7%单调下降到最高分段的4.9%',
        'Good/Bad箱线图中位数差异显著',
        '相关性: -0.283 (负相关, 分数越高越安全)',
    ])
    pdf.analysis_box('近6月查询次数 (inq_6m)', [
        '坏账率从低分段的13.1%上升到高分段的26.9%',
        '查询次数多=在大量借钱=高风险信号',
        '异常值比例6.55%, 但高值不要盲目缩尾——恰恰是风险信号',
    ])
    pdf.analysis_box('负债收入比 (DTI)', [
        '坏账率随DTI上升单调递增 (10.9% -> 26.6%)',
        '反映了还款压力与违约风险的正相关',
        '相关性: +0.150',
    ])
    pdf.analysis_box('循环额度利用率 (revol_util)', [
        '坏账率从低分段的11.6%上升到高分段的24.7%',
        '信用卡刷得越满, 还款压力越大',
        '相关性: +0.125',
    ])
    pdf.analysis_box('年收入 (annual_inc)', [
        '坏账率随收入上升而下降 (20.9% -> 12.0%)',
        '收入越高还款能力越强, 符合业务逻辑',
        '但注意: 自报收入可能存在虚报, 区分度有限',
    ])

    # ====== 第4章: 缺失值分析 ======
    pdf.add_page()
    pdf.section_title('4. 缺失值分析 -- 缺失本身也有信息量')

    pdf.body('风控数据几乎不可能没有缺失值。关键在于区分"为什么缺失"——不同原因的缺失需要不同的处理策略。')

    pdf.sub_title('缺失值三大类型')

    pdf.set_font('CN', 'B', 10)
    pdf.set_text_color(40, 120, 80)
    pdf.cell(0, 7, '类型1: 结构性缺失 (如: 没有循环信用 -> revol_util为空)', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('CN', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.body('这个客户根本没有信用卡, 自然没有"循环额度利用率"这个值。直接填0或用单独类别"NoRevolving"标记。处理策略: 填充0或单独类别')

    pdf.set_font('CN', 'B', 10)
    pdf.set_text_color(40, 120, 80)
    pdf.cell(0, 7, '类型2: 随机缺失 (如: 系统录入遗漏)', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('CN', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.body('数据在录入时偶发性丢失, 与客户本身属性无关。中位数/众数填充, 或用KNN等模型预测填充。处理策略: 中位数/众数填充')

    pdf.set_font('CN', 'B', 10)
    pdf.set_text_color(180, 70, 30)
    pdf.cell(0, 7, '类型3: 信息性缺失 (如: 故意不填收入, 可能本身就是高风险)', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('CN', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.body('这是最容易被忽略但最重要的类型。不填收入的客户可能本身就是自由职业者或不愿透露财务状况的人。保留缺失标记作为独立特征, 同时填充特殊值(-9999)。处理策略: 保留缺失标记 + 特殊值填充')

    pdf.key_point('面试加分回答: "缺失值处理不是简单的填均值。我会先分析缺失是否有业务含义——比如收入缺失可能本身就意味着自由职业者或信息隐瞒, 这类客户的风险往往不同。我会把缺失标记保留为一个特征放入模型, 比盲目填充效果好得多。"')

    # ====== 第5章: 异常值处理 ======
    pdf.section_title('5. 异常值检测 -- 区分三类"异常"')

    pdf.body('异常值不等于错误值。风控里的"异常"有时候恰恰是最有信息量的。处理前必须先分类:')

    pdf.sub_title('三类异常值的处理策略')
    pdf.code_block(
        '类别              示例              处理方式\n'
        '─────────────────────────────────────────────────\n'
        '数据错误           年龄=200           直接修正或剔除\n'
        '(Data Error)       收入=-10000         (数据质量问题)\n'
        '\n'
        '业务极端值         FICO=850            1%/99% winsorize\n'
        '(Biz Extreme)      收入=500万          (合法但极端)\n'
        '\n'
        '风险信号           查询次数=10         绝对不能删!\n'
        '(Risk Signal)      逾期次数=5          (这恰恰是预测力来源)\n'
    )

    pdf.sub_title('IQR异常值判定')
    pdf.body('统计方法: 计算Q1(25分位)、Q3(75分位)和IQR=Q3-Q1。下界=Q1-1.5*IQR, 上界=Q3+1.5*IQR。超出此范围的标记为异常值。注意: 这只是统计视角, 最终还是要结合业务含义判断。')

    pdf.sub_title('本项目异常值检测结果')
    pdf.code_block(
        '变量              异常比例    处理建议\n'
        'inq_6m            6.55%      风险信号, 保留不缩尾\n'
        'loan_amnt         6.21%      长尾分布, 对数变换\n'
        'annual_inc        3.49%      缩尾处理(1%/99%)\n'
        'delinq_2yrs       1.38%      风险信号, 保留\n'
        'fico_score        0.71%      可正常处理\n'
    )

    pdf.key_point('核心原则: 缩尾(winsorize)前一定要问自己——这个高值代表风险信号还是随机噪声？如果是风险信号, 缩尾等于主动扔掉模型的区分能力。')

    # ====== 第6章: 相关性分析 ======
    pdf.add_page()
    pdf.section_title('6. 相关性分析 -- 量化变量预测力')

    pdf.body('通过Pearson相关系数量化每个数值变量与目标变量(Bad)的线性相关程度。这为后续的特征筛选提供初步参考。')

    pdf.sub_title('本项目相关性排名')
    pdf.code_block(
        '变量            相关系数    方向        解读\n'
        'fico_score       -0.283     负相关      分数越高越安全 (最强)\n'
        'inq_6m           +0.157     正相关      查询越多越危险\n'
        'delinq_2yrs      +0.153     正相关      历史逾期多 -> 未来风险高\n'
        'dti              +0.150     正相关      负债压力大 -> 违约风险高\n'
        'revol_util       +0.125     正相关      信用卡刷满 -> 现金流紧张\n'
        'credit_age       -0.102     负相关      信用历史长 -> 更可靠\n'
        'annual_inc       -0.091     负相关      收入越高越安全\n'
        'int_rate         -0.004     几乎无关    (合成数据局限)\n'
        'loan_amnt        -0.000     几乎无关    (合成数据局限)\n'
    )

    pdf.body('注意: 相关系数低不等于变量没用。相关系数只衡量线性关系, 但风险信号往往是非线性的。这就是为什么后续要用WOE和IV来做更精准的衡量。')

    pdf.key_point('面试常问: "相关性高的两个变量, 留哪个?" 答案: 分别看IV, 留IV高的那个。如果IV接近, 优先留业务可解释性好的、数据质量高的。如果两个变量高度相关(>0.7)且含义重叠, 考虑合并或只留一个。')

    # ====== 第7章: 面试高频问答 ======
    pdf.add_page()
    pdf.section_title('7. 面试高频问答')

    pdf.qa_block(
        '怎么从数据中验证好坏客户定义？Roll Rate怎么算？',
        '用Roll Rate(逾期迁移率)分析。方法: 1)将每期DPD转为M0-M4+阶段; 2)统计相邻月份间各阶段的转移概率; 3)看从M0各阶段向M3+的迁移率。如果M2->M3+迁移率>60%, 说明M2已是事实上的坏客户; 如果<30%, 则M3+是合理的阈值。银行每季度更新此报告来监控资产质量。'
    )

    pdf.qa_block(
        'Vintage分析是什么？怎么看一张Vintage图？',
        'Vintage按放款月份分组, 追踪每个批次在不同账龄(MOB)的累计坏账率。四步解读: 1)看趋势--曲线收敛说明风控稳定, 发散说明策略变化或客群漂移; 2)看陡峭度--曲线越陡客群越差; 3)看MOB6--大部分坏账在6个月暴露; 4)看MOB12--用于最终损失率估计和拨备计提。如果最近几个月曲线明显高于历史, 需要立刻排查原因。'
    )

    pdf.qa_block(
        '缺失值怎么处理？为什么不能都填均值？',
        '缺失值处理的前提是区分缺失类型: 结构性缺失(如无信用卡->revol_util空)填0; 随机缺失(系统遗漏)填中位数; 信息性缺失(故意不填收入可能是高风险)要保留缺失标记作特征。填均值的最大问题是: 它假设缺失是随机的, 但风控数据中缺失往往有业务含义。把缺失当作一个独立特征, IV往往比你想象的高。'
    )

    pdf.qa_block(
        '异常值怎么处理？什么时候缩尾, 什么时候不缩尾？',
        '先分类: 数据错误(年龄=200)直接修正; 业务极端值(FICO=850)用1%/99% winsorize缩尾; 风险信号(查询次数=10)绝对不能缩尾。核心判断标准: 这个高值代表风险信号还是随机噪声? 如果是风险信号, 缩尾等于扔掉模型的区分能力。面试中说清楚这三类区分, 比单纯说用IQR判异常要高级得多。'
    )

    pdf.qa_block(
        'FICO分为什么是风控最重要的单一指标？',
        'FICO分综合了5大维度: 还款历史(35%)、负债水平(30%)、信用历史长度(15%)、新信用(10%)、信用类型(10%)。它是经过数十年数据验证的标准化信用风险浓缩指标。本项目中也证实FICO分是最强单变量预测因子(相关系数-0.283), 坏账率从最低分段34.7%单调降至4.9%。在中国对应的是央行征信分和百行征信分。'
    )

    # ====== 第8章: 简历成果 ======
    pdf.add_page()
    pdf.section_title('8. 简历成果提炼')

    pdf.sub_title('中文版 (追加到简历项目经验)')
    pdf.code_block(
        '信用评分卡系统开发 -- EDA与风险画像\n'
        '\n'
        '- 运用Roll Rate Analysis构建逾期迁移矩阵，以数据驱动方式验证\n'
        '  M3+(DPD>=90)坏客户定义标准的合理性\n'
        '- 完成24个放款批次的Vintage分析，追踪MOB1-MOB12累计坏账率变化\n'
        '  趋势，评估风控策略稳定性及资产组合质量\n'
        '- 对9个连续变量和4个分类变量执行单变量风险分析，通过分箱统计、\n'
        '  箱线图对比识别高区分度特征(FICO分/查询次数/DTI等)\n'
        '- 建立缺失值分类处理框架(结构性/随机性/信息性)和异常值三级识别\n'
        '  体系(数据错误/业务极端值/风险信号)'
    )

    pdf.sub_title('英文版 (English Resume)')
    pdf.code_block(
        'Credit Scorecard System - EDA & Risk Profiling\n'
        '\n'
        '- Performed Roll Rate Analysis to construct delinquency migration matrix,\n'
        '  empirically validating M3+ (DPD>=90) as the optimal bad definition threshold\n'
        '- Conducted Vintage analysis across 24 origination cohorts, tracking MOB1-12\n'
        '  cumulative default rates to assess portfolio quality and strategy stability\n'
        '- Analyzed 9 continuous & 4 categorical variables via binning & boxplot comparison,\n'
        '  identifying high-discrimination features: FICO score, inquiries, DTI, revol util\n'
        '- Established a 3-tier missing-value framework (structural/random/informative) and\n'
        '  outlier classification system (data error / biz extreme / risk signal)'
    )

    pdf.sub_title('面试中的项目描述模板')
    pdf.body('"在建模前我做了完整的EDA。首先用Roll Rate分析构建了逾期迁移矩阵，从数据上验证了M3+作为坏客户定义的合理性——M0客户95.3%维持正常，而M3+几乎不回滚。然后用Vintage分析追踪了24个放款批次的12期账龄表现，MOB12坏账率在3.5%-5.4%之间，曲线收敛说明风控策略稳定。最后通过单变量分析确定了FICO分、查询次数、DTI等高区分度特征，为后续的特征工程和评分卡建模提供了清晰方向。"')

    # ====== 尾页 ======
    pdf.add_page()
    pdf.ln(20)
    pdf.title_block('Phase 2 完成')
    pdf.ln(10)
    pdf.set_font('CN', '', 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, '下一阶段: Phase 3 -- 特征工程与WOE/IV', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 8, '变量分箱 / WOE编码 / IV筛选 / VIF检验 / 相关性分析', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(15)

    pdf.set_font('CN', '', 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 6, '技术栈: Python 3.13 | SQLite | pandas | matplotlib | seaborn', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 6, '项目路径: F:\\claude\\credit-scorecard\\', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 6, '配套 Notebook: 02_eda_risk_profile.ipynb', new_x="LMARGIN", new_y="NEXT", align='C')

    # 保存
    output_path = 'F:/claude/Phase2_EDA与风险画像.pdf'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    print(f'[OK] PDF已生成: {output_path}')
    return output_path


if __name__ == '__main__':
    generate()
