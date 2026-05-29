"""
项目全局配置文件
在真实公司里，配置集中在配置中心(如Nacos/Apollo)，这里用单一config.py模拟
"""
import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 数据路径
DATA_RAW = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "risk_db.sqlite")

# 数据库连接字符串
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ---- 风控核心参数 ----

# 好坏客户定义 (这是风控最基本也最重要的业务决策)
# M3+ (逾期90天以上) 定义为"坏" — 行业标准做法
# 为什么是M3+而不是M1+? M1可能是忘记还款，M3+才是真正的还款意愿问题
BAD_DPD_THRESHOLD = 90   # DPD=Days Past Due, 逾期天数阈值
GOOD_DPD_THRESHOLD = 30  # 逾期<30天定义为"好"

# 时间窗口
# 观察期(Observation Window): 看借款人的历史行为 — 通常是借款前12-24个月
OBSERVATION_MONTHS = 24
# 表现期(Performance Window): 看借款后的还款表现 — 通常6-12个月
PERFORMANCE_MONTHS = 12

# 评分卡参数
# Base Score: 基准分，通常设为600或660
BASE_SCORE = 600
# PDO (Points to Double Odds): 分数每增加PDO，好坏比翻倍
# PDO越小，分数区分度越大（银行通常用20-50）
PDO = 20
# 基准Odds (好坏比)，行业通常设为1:1到1:5
BASE_ODDS = 5   # 5个好客户对应1个坏客户 (匹配portfolio实际坏账率~17%)

# 模型监控阈值
PSI_ALERT = 0.1   # PSI>0.1 需要关注
PSI_REBUILD = 0.25  # PSI>0.25 需要重建模型
KS_MIN = 0.25       # 模型最低KS要求

# 风险等级划分 (分数越高风险越低)
RISK_GRADES = {
    "A": (680, 1000, "极低风险", 0.05),   # (下限, 上限, 描述, 预期坏账率)
    "B": (640, 680, "低风险", 0.08),
    "C": (600, 640, "中等风险", 0.12),
    "D": (560, 600, "较高风险", 0.18),
    "E": (300, 560, "高风险", 0.30),
}
