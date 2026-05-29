"""
生成 Phase 1 & Phase 2 操作手册 PDF
输出: F:/claude/操作手册_Phase1_风控数据基础.pdf
      F:/claude/操作手册_Phase2_EDA与风险画像.pdf
"""
from fpdf import FPDF
import os

class ManualPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.add_font('CN', '', 'C:/Windows/Fonts/simhei.ttf')
        self.add_font('CN', 'B', 'C:/Windows/Fonts/simhei.ttf')
        self.set_auto_page_break(True, 22)
        self._in_code = False

    def cover(self, phase_num, title, subtitle):
        self.add_page()
        self.ln(25)
        self.set_font('CN', 'B', 26)
        self.set_text_color(25, 60, 120)
        self.cell(0, 14, f'Phase {phase_num} 操作手册', new_x="LMARGIN", new_y="NEXT", align='C')
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
        self.cell(0, 7, '信用评分卡项目 | 导师制教学 | 零基础可操作', new_x="LMARGIN", new_y="NEXT", align='C')
        self.cell(0, 7, '每一步标注了"为什么这样做"和"真实公司里怎么做"', new_x="LMARGIN", new_y="NEXT", align='C')

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
        self.cell(0, 9, f'  步骤 {num}：{title}', new_x="LMARGIN", new_y="NEXT", fill=True)
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
        self.multi_cell(self.w - self.r_margin - left, 5.5, f'[说明] {text}', fill=True)
        self.ln(1)
        self.set_text_color(60, 60, 60)

    def warn(self, text):
        self.ln(1)
        self.set_font('CN', 'B', 9.5)
        self.set_text_color(180, 70, 30)
        self.set_fill_color(255, 245, 235)
        left = self.l_margin
        self.set_x(left)
        self.multi_cell(self.w - self.r_margin - left, 5.5, f'[重要] {text}', fill=True)
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


# ==================== PHASE 1 ====================
def generate_phase1():
    pdf = ManualPDF()
    pdf.set_margin(20)

    pdf.cover(1, '风控数据基础', '预计耗时 1.5-2小时 | 最终产出：风控数据库 + SQL风险分析')

    # ---- 准备 ----
    pdf.h1('准备工作：确认环境')
    pdf.step_header(1, '打开终端')
    pdf.body('按键盘上的 Win + R 键，输入 powershell，然后按回车。会弹出一个命令行窗口。')
    pdf.body('Win键就是键盘左下角带Windows图标的那个键。')

    pdf.step_header(2, '检查 Python')
    pdf.body('在终端中输入以下命令并回车：')
    pdf.code('python --version')
    pdf.note('应该显示 Python 3.13.x。如果显示"找不到命令"，说明 Python 没安装。')

    pdf.step_header(3, '进入项目目录')
    pdf.body('输入以下命令并回车，把终端"移动"到项目文件夹里：')
    pdf.code('cd F:\\claude\\credit-scorecard')
    pdf.note('cd = Change Directory，切换工作目录。后续所有操作都在这个文件夹里执行。')

    # ---- 第一步 ----
    pdf.h1('第一步：激活虚拟环境')
    pdf.step_header(4, '激活 venv')
    pdf.body('虚拟环境是项目专属的 Python 运行环境，隔离了项目依赖，不会和你电脑上其他 Python 项目冲突。')
    pdf.code('.\\venv\\Scripts\\Activate.ps1')
    pdf.note('激活成功后，终端提示符前面会出现 (venv) 标记。')
    pdf.warn('如果提示权限错误，先运行 Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned，输入 Y 确认，然后再激活。')

    # ---- 第二步 ----
    pdf.h1('第二步：运行数据加载（只做一次）')
    pdf.step_header(5, '生成风控数据并创建数据库')
    pdf.body('这个脚本会：生成50,000条借贷数据 → 创建SQLite数据库 → 建立三张风控核心表。等待约30秒。')
    pdf.code('python src\\data_loader.py')
    pdf.body('你会看到如下输出，表示成功：')
    pdf.output_line('[INFO] 生成 50000 条合成借贷数据')
    pdf.output_line('[INFO] 合成数据坏账率: 17.18%')
    pdf.output_line('[OK] 合成数据已保存')
    pdf.output_line('[INFO] 创建风控数据库')
    pdf.output_line('  申请表: 50000 条')
    pdf.output_line('  借据表: 50000 条')
    pdf.output_line('  还款表: 600000 条')
    pdf.output_line('[OK] 风控数据库创建完成!')
    pdf.warn('这一步只做一次！以后不需要重复运行，数据库已经建好了。')

    # ---- 第三步 ----
    pdf.h1('第三步：用 SQL 探索数据库')
    pdf.body('现在你有了一个真实的数据库，可以用 SQL 来探索数据。不需要打开 Excel 或任何大型软件——直接在终端里写 Python 就行。')

    pdf.step_header(6, '启动 Python 交互环境')
    pdf.body('在终端中输入（确保虚拟环境已激活）：')
    pdf.code('python')
    pdf.body('你会看到 >>> 提示符，表示现在在 Python 里面了。接下来一行行输入代码。')

    pdf.step_header(7, '连接数据库')
    pdf.body('逐行输入以下代码（每行输完按回车）：')
    pdf.code(
        '# 导入工具包\n'
        '# sqlite3: Python自带的数据库工具\n'
        '# pandas: 数据分析库，可以像操作Excel一样操作数据\n'
        'import sqlite3\n'
        'import pandas as pd\n'
        '\n'
        '# 连接数据库 — 相当于"打开文件"\n'
        '# data/risk_db.sqlite 是我们刚才创建的数据库文件\n'
        "conn = sqlite3.connect('data/risk_db.sqlite')\n"
        '\n'
        '# 查看库里有哪些表\n'
        "tables = pd.read_sql_query(\n"
        '    \"SELECT name FROM sqlite_master WHERE type=\'table\'\",\n'
        '    conn\n'
        ')\n'
        'print(tables)'
    )
    pdf.body('输出应该是：')
    pdf.output_line('               name')
    pdf.output_line('0   sqlite_sequence')
    pdf.output_line('1      apply_table')
    pdf.output_line('2       loan_table')
    pdf.output_line('3  repayment_table')

    pdf.step_header(8, '查看每张表有多少行')
    pdf.code(
        '# 循环遍历三张表，分别查行数\n'
        '# COUNT(*) = 统计总行数\n'
        '# f-string (f"...") = 格式化字符串，把变量值嵌进去\n'
        "for table_name in ['apply_table', 'loan_table', 'repayment_table']:\n"
        '    result = pd.read_sql_query(\n'
        '        f"SELECT COUNT(*) as cnt FROM {table_name}",\n'
        '        conn\n'
        '    )\n'
        '    # iloc[0,0] = 取DataFrame第0行第0列的值\n'
        '    # :, = 给数字加千分位逗号(如 50000 显示为 50,000)\n'
        '    print(f"{table_name}: {result.iloc[0,0]:,} 行")'
    )

    pdf.step_header(9, '计算整体坏账率')
    pdf.body('这是风控最基础的指标——整个资产组合里有多少是坏账。')
    pdf.code(
        'overview = pd.read_sql_query(\"\"\"\n'
        '    SELECT\n'
        '        loan_status,               -- 好/坏标签\n'
        '        COUNT(*) as 数量,          -- 统计每个标签有多少条\n'
        '        ROUND(                     -- ROUND = 四舍五入\n'
        '            COUNT(*) * 100.0 /     -- 算百分比\n'
        '            SUM(COUNT(*)) OVER(),  -- 总行数(分母)\n'
        '            2                       -- 保留2位小数\n'
        '        ) as 占比\n'
        '    FROM loan_table\n'
        '    GROUP BY loan_status           -- 按好/坏分组\n'
        '\"\"\", conn)\n'
        'print(overview)'
    )

    pdf.step_header(10, '按 FICO 分段分析坏账率')
    pdf.body('FICO信用分是衡量个人信用的核心指标。我们把它分成5段，看每段里坏客户占比多少。')
    pdf.code(
        'fico_analysis = pd.read_sql_query(\"\"\"\n'
        '    SELECT\n'
        '        CASE                                    -- CASE = 分类判断\n'
        '            WHEN fico_score < 620 THEN \'<620\'\n'
        '            WHEN fico_score < 660 THEN \'620-660\'\n'
        '            WHEN fico_score < 700 THEN \'660-700\'\n'
        '            WHEN fico_score < 740 THEN \'700-740\'\n'
        '            ELSE \'740+\'\n'
        '        END as FICO分段,\n'
        '        COUNT(*) as 样本数,\n'
        '        ROUND(\n'
        '            AVG(CASE WHEN loan_status=\'Bad\' THEN 1.0 ELSE 0.0 END)\n'
        '            * 100, 2\n'
        '        ) as 坏账率\n'
        '    FROM loan_table\n'
        '    GROUP BY FICO分段\n'
        '    ORDER BY MIN(fico_score)\n'
        '\"\"\", conn)\n'
        'print(fico_analysis)'
    )
    pdf.body('你应该看到：分数越低 → 坏账率越高。这就是风控的核心规律。')
    pdf.note('AVG(CASE WHEN...) 是计算坏账率的常用写法：把 Bad 变成 1，Good 变成 0，求平均就是坏账比例。')

    pdf.step_header(11, '退出 Python')
    pdf.code(
        'conn.close()   # 关闭数据库连接，养成好习惯\n'
        'exit()          # 退出 Python，回到终端'
    )

    # ---- 第四步 ----
    pdf.h1('第四步（可选）：用 Jupyter Notebook 学习')
    pdf.body('Jupyter Notebook 是一个可以在浏览器里边写代码边看结果的交互式文档，更适合初学者。')
    pdf.step_header(12, '安装并启动 Jupyter')
    pdf.code(
        '# 确保在项目目录且虚拟环境已激活\n'
        'pip install jupyter -q\n'
        '\n'
        '# 启动 Jupyter（浏览器会自动打开）\n'
        'jupyter notebook'
    )
    pdf.body('浏览器打开后：点击 notebooks 文件夹 → 点击 01_data_overview.ipynb → 从上到下按 Shift+Enter 逐个运行代码框。')

    # ---- 知识自检 ----
    pdf.add_page()
    pdf.h1('知识自检清单')
    pdf.body('完成以上操作后，试着回答以下问题：')
    pdf.check_item('风控数据仓库有哪三张核心表？分别存什么信息？')
    pdf.check_item('为什么 apply_table 要存"申请时刻的快照"而不是实时数据？')
    pdf.check_item('观察期(24个月)和表现期(12个月)分别是什么？为什么需要这两个窗口？')
    pdf.check_item('坏客户的定义是什么？为什么是 M3+(逾期90天)而不是 M1+(30天)？')
    pdf.check_item('什么是数据穿越(Data Leakage)？为什么它是风控建模中最严重的错误？')
    pdf.check_item('如何用 SQL 的 CASE WHEN + AVG 计算某个维度的坏账率？')

    pdf.ln(5)
    pdf.h1('你完成了什么')
    pdf.bullet('生成了 50,000 条借贷数据，包含 19 个变量')
    pdf.bullet('在 SQLite 中创建了 3 张风控核心表：申请表、借据表、还款表')
    pdf.bullet('用 SQL 查询了整体坏账率（约 17.18%）')
    pdf.bullet('按 FICO 分段分析了坏账率的单调递减关系')
    pdf.bullet('理解了风控最核心的时间窗口概念')
    pdf.ln(3)
    pdf.warn('简历可写：设计并搭建风控数据仓库模型（申请-借据-还款三层架构），管理5万笔借贷申请及60万条还款记录，使用SQL完成信贷资产风险画像初步分析，按FICO分段/借款目的维度拆解坏账率分布。')

    pdf.ln(5)
    pdf.set_font('CN', 'B', 12)
    pdf.set_text_color(40, 90, 160)
    pdf.cell(0, 8, 'Phase 2 操作手册见下一页 →', new_x="LMARGIN", new_y="NEXT", align='C')

    output = 'F:/claude/操作手册_Phase1_风控数据基础.pdf'
    pdf.output(output)
    print(f'[OK] Phase 1 手册: {output}')
    return output


# ==================== PHASE 2 ====================
def generate_phase2():
    pdf = ManualPDF()
    pdf.set_margin(20)

    pdf.cover(2, 'EDA与风险画像', '预计耗时 2-3小时 | 最终产出：Roll Rate矩阵 + Vintage图 + 单变量分析报告')

    # ---- 前置条件 ----
    pdf.h1('前置条件')
    pdf.body('开始前确认以下事项：')
    pdf.bullet('已完成 Phase 1，数据库文件 data/risk_db.sqlite 存在')
    pdf.bullet('虚拟环境已激活（终端显示 (venv) 标记）')
    pdf.bullet('当前在项目目录下：F:\\claude\\credit-scorecard\\')
    pdf.warn('如果虚拟环境未激活：cd F:\\claude\\credit-scorecard 然后 .\\venv\\Scripts\\Activate.ps1')

    # ---- 方式一 ----
    pdf.h1('方式一：运行验证脚本（5分钟快速体验）')
    pdf.body('我们已经为你写好了完整的分析脚本，一行命令即可运行全部6大分析：')
    pdf.step_header(1, '运行 Phase 2 验证脚本')
    pdf.code('python src\\test_phase2.py')
    pdf.body('你会看到 Roll Rate 矩阵、Vintage 统计、单变量分析、相关性排名等全部结果。')
    pdf.note('这个脚本是帮你快速验证用的。要真正理解和掌握，建议按下面的方式二一步步操作。')

    # ---- 方式二 ----
    pdf.h1('方式二：用 Jupyter Notebook 逐步操作（推荐学习用）')
    pdf.body('这是最主要的学习方式——打开 Notebook，逐个代码框运行，边看结果边读解释。')

    pdf.step_header(2, '安装并启动 Jupyter（如未安装）')
    pdf.code(
        'pip install jupyter -q\n'
        'jupyter notebook'
    )
    pdf.body('浏览器自动打开后，进入 notebooks 文件夹，点击 02_eda_risk_profile.ipynb。')

    pdf.step_header(3, '运行 Notebook 的正确方式')
    pdf.body('Notebook 打开后，你会看到代码框和文字交错排列。从上到下，点击每个代码框，按 Shift + Enter 执行。不要跳着运行，因为后面的代码依赖前面的变量。')
    pdf.warn('如果中文在图上显示为方框，这是正常现象——你的电脑上可能缺少中文字体。不影响数据分析结果，只是图表标题显示为方框。')

    # ---- 六大分析详解 ----
    pdf.add_page()
    pdf.h1('六大分析模块详解')

    # 分析1
    pdf.h2('分析1：Roll Rate — 逾期迁移率分析')
    pdf.body('目的：用数据验证"M3+(90天)是合理的坏客户定义"这个假设。')
    pdf.body('Roll Rate = 当前处于某逾期阶段的客户，下个月滚到更严重阶段的概率。')
    pdf.code(
        '# 核心逻辑（Notebook 中自动执行，这里展示关键步骤）\n'
        '\n'
        '# 1. 把每笔借据的12期还款记录排成一行\n'
        'dpd_pivot = repay.pivot(index=\'loan_id\', columns=\'period\', values=\'dpd\')\n'
        '\n'
        '# 2. 把DPD天数转为逾期阶段 M0/M1/M2/M3/M4+\n'
        'def dpd_to_stage(dpd_val):\n'
        '    if pd.isna(dpd_val): return None\n'
        '    if dpd_val == 0: return \'M0\'      # 按时还\n'
        '    if dpd_val <= 30: return \'M1\'      # 逾期1-30天\n'
        '    if dpd_val <= 60: return \'M2\'      # 逾期31-60天\n'
        '    if dpd_val <= 90: return \'M3\'      # 逾期61-90天\n'
        '    return \'M4+\'                        # 逾期90天以上\n'
        '\n'
        '# 3. 计算迁移矩阵：第N期状态 -> 第N+1期状态的概率\n'
        'flow = pd.crosstab(stage_pivot[col], stage_pivot[col+1], normalize=\'index\')'
    )
    pdf.body('看结果时关注：M2行M3+M4+列的和——如果>60%，说明M2已经是事实上的坏客户；如果<30%，M3+才是合理阈值。')
    pdf.note('面试怎么讲：我们通过Roll Rate分析验证了M3+的坏客户定义——M0客户95.3%维持正常，而M3+几乎不回滚，说明M3+是明确的坏客户分界点。')

    # 分析2
    pdf.h2('分析2：Vintage — 资产质量趋势分析')
    pdf.body('目的：按放款月份分组，追踪每个批次在不同账龄(MOB)的累计坏账率变化。')
    pdf.body('这是银行/消费金融公司最核心的资产质量评估工具——每季度董事会上必看的图。')
    pdf.code(
        '# 核心逻辑\n'
        '\n'
        '# 1. 对每笔借据，算它每期还款时的账龄(MOB)\n'
        "# MOB = Month-on-Book = 放款后的第几个月\n"
        "repay_detail['mob'] = (\n"
        "    (还款日期.年 - 放款日期.年) * 12 +\n"
        "    (还款日期.月 - 放款日期.月)\n"
        ")\n"
        '\n'
        '# 2. 按 放款月份 + MOB 分组统计累计坏账率\n'
        '#    按放款月份分组 = 同一批放款的客户放一起\n'
        '#    DPD>=90 = M3+ = 坏客户\n'
        'for (放款月份, 账龄), 数据 in repay_detail.groupby([放款月份, 账龄]):\n'
        '    累计坏账率 = 该组内DPD>=90的借据数 / 该组总借据数\n'
        '\n'
        '# 3. 画图：X轴=MOB(1-12), Y轴=坏账率, 每条线=一个放款月份\n'
        'ax.plot(data[\'mob\'], data[\'bad_rate\'] * 100)'
    )
    pdf.body('Vintage图读法（四步法）：')
    pdf.bullet('看趋势：曲线收敛 = 风控稳定；发散 = 策略变化或客群漂移')
    pdf.bullet('看陡峭度：曲线越陡 = 坏账暴露越快 = 客群质量越差')
    pdf.bullet('看MOB6：行业标准benchmark，大部分坏账在6个月内暴露')
    pdf.bullet('看MOB12：用于最终损失率估计和拨备计提')
    pdf.warn('如果某个月份的Vintage曲线明显高于历史平均值，需要立刻排查——可能是该月风控策略放松了，或者渠道引入了低质量客户。')

    # 分析3
    pdf.h2('分析3：单变量分析 — 逐个变量 vs 坏账率')
    pdf.body('目的：理解每个变量与违约的关系，判断哪些变量的区分度好。')
    pdf.body('方法：数值变量分10箱，每箱算坏账率看趋势；类别变量分组算坏账率看差异。')
    pdf.code(
        '# 关键代码（Notebook中自动执行）\n'
        '\n'
        '# 把变量等频分成10份(箱)\n'
        "# qcut = Quantile Cut = 保证每箱样本量基本相同\n"
        "data['bin'] = pd.qcut(data[变量], q=10, duplicates='drop')\n"
        '\n'
        '# 每箱算坏账率\n'
        "bin_stats = data.groupby('bin')['is_bad'].agg(['mean', 'count'])\n"
        '\n'
        '# 画柱状图(样本量) + 折线图(坏账率) 双Y轴图\n'
        'ax2 = ax.twinx()  # 创建共享X轴的第二Y轴\n'
        'ax.bar(x, 样本量, alpha=0.3, color=\'steelblue\')    # 柱子=样本量\n'
        "ax2.plot(x, 坏账率, 'ro-', linewidth=2)            # 折线=坏账率"
    )
    pdf.body('看什么：')
    pdf.bullet('单调性：坏账率应该随变量值单调变化（如FICO越高坏账率越低）')
    pdf.bullet('区分度：最高箱和最低箱的坏账率差距越大越好')
    pdf.bullet('U型/U型异常：如果坏账率先降后升，需要检查是否有隐藏变量在起作用')

    # 分析4
    pdf.h2('分析4：缺失值分析 — 缺失本身也有信息量')
    pdf.body('目的：风控数据几乎不可能没有缺失值。关键不是有没有缺失，而是为什么缺失。')
    pdf.body('缺失值三大类型及处理策略：')
    pdf.bullet('结构性缺失（如无信用卡→revol_util为空）：填充0或标为"NoRevolving"')
    pdf.bullet('随机缺失（系统录入遗漏）：中位数/众数填充')
    pdf.bullet('信息性缺失（故意不填收入，本身可能是高风险）：保留缺失标记+填充-9999')
    pdf.warn('面试加分回答：把缺失标记作为一个独立特征放入模型。比如"收入是否缺失"这个二值变量的IV往往比你想象的高——因为不填收入的人本身就有风险特征。')

    pdf.add_page()
    # 分析5
    pdf.h2('分析5：异常值检测 — 区分三类"异常"')
    pdf.body('目的：异常值不等于错误值。处理前必须先分类。')
    pdf.code(
        '数据错误    如年龄=200            直接修正或剔除\n'
        '业务极端值  如FICO=850            1%/99%缩尾(winsorize)\n'
        '风险信号    如查询次数=10          绝对不能删！'
    )
    pdf.body('IQR判定方法：')
    pdf.bullet('Q1 = 25分位数，Q3 = 75分位数，IQR = Q3 - Q1')
    pdf.bullet('下界 = Q1 - 1.5 x IQR，上界 = Q3 + 1.5 x IQR')
    pdf.bullet('超出上下界的标记为统计意义上的异常值')
    pdf.warn('核心原则：缩尾前一定要问——这个高值代表风险信号还是随机噪声？inq_6m=10查询次数的客户恰恰是最危险的，缩尾等于扔掉模型的区分能力。')

    # 分析6
    pdf.h2('分析6：相关性分析 — 量化每个变量的预测力')
    pdf.body('目的：计算每个数值变量与目标(Bad)的Pearson相关系数，初步判断变量重要性。')
    pdf.code(
        '# 计算所有变量之间的相关性矩阵\n'
        'corr = df[变量列表].corr()\n'
        '\n'
        '# 取出与 is_bad 的相关性并排序\n'
        "target_corr = corr['is_bad'].drop('is_bad').sort_values(ascending=False)\n"
        '\n'
        '# 正值=正相关(变量值越高越危险)\n'
        '# 负值=负相关(变量值越高越安全)\n'
        '# 绝对值越大=预测力越强'
    )
    pdf.body('本项目相关性排名：')
    pdf.bullet('fico_score: -0.283（负相关，分数越高越安全）★最强')
    pdf.bullet('inq_6m: +0.157（正相关，查询越多越危险）')
    pdf.bullet('delinq_2yrs: +0.153（正相关，历史逾期多=未来风险高）')
    pdf.bullet('dti: +0.150（正相关，负债压力大=违约风险高）')
    pdf.note('相关系数低≠变量没用。相关系数只衡量线性关系，很多风险信号是非线性的。这就是下一步 Phase 3 要用 WOE/IV 的原因。')

    # 知识自检
    pdf.add_page()
    pdf.h1('知识自检清单')
    pdf.check_item('什么是 Roll Rate？它是怎么计算的？')
    pdf.check_item('怎么从 Roll Rate 矩阵中判断 M3+ 是否是合理的坏客户定义？')
    pdf.check_item('Vintage 分析的四步解读法是什么？')
    pdf.check_item('Vintage 曲线收敛 vs 发散分别说明什么？')
    pdf.check_item('数值变量分箱后怎么看单调性和区分度？')
    pdf.check_item('缺失值有哪三种类型？各自的处理策略是什么？')
    pdf.check_item('异常值处理前为什么要先分三类？哪三类不能随便缩尾？')
    pdf.check_item('Pearson 相关系数的局限性是什么？为什么还需要 WOE/IV？')

    pdf.ln(5)
    pdf.h1('你完成了什么')
    pdf.bullet('Roll Rate Analysis：构建了逾期迁移矩阵，从数据上验证了M3+坏客户定义')
    pdf.bullet('Vintage Analysis：追踪了24个放款批次12期账龄的坏账率变化')
    pdf.bullet('单变量分析：对9个数值变量+4个类别变量做了分箱坏账率分析')
    pdf.bullet('缺失值框架：建立了结构性/随机性/信息性三级分类处理思路')
    pdf.bullet('异常值体系：掌握了数据错误/业务极端值/风险信号三级区分方法')
    pdf.bullet('相关性排名：量化了各变量的预测力，FICO分(-0.283)是最强预测因子')
    pdf.ln(3)
    pdf.warn('简历可写：完成信贷资产深度风险画像，通过Roll Rate Analysis验证M3+坏客户定义，使用Vintage分析追踪24个放款批次的累计坏账率变化趋势，对9个变量完成单变量风险分析，识别出FICO分/查询次数/DTI等高区分度特征，建立缺失值三级分类框架和异常值三级识别体系。')

    output = 'F:/claude/操作手册_Phase2_EDA与风险画像.pdf'
    pdf.output(output)
    print(f'[OK] Phase 2 手册: {output}')
    return output


if __name__ == '__main__':
    generate_phase1()
    generate_phase2()
    print('\n两份操作手册PDF已全部生成！')
