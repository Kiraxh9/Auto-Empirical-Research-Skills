from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

FONT_REG = "/tmp/expo-sc/package/400Regular/NotoSansSC_400Regular.ttf"
FONT_MED = "/tmp/expo-sc/package/500Medium/NotoSansSC_500Medium.ttf"
FONT_BOLD = "/tmp/expo-sc/package/700Bold/NotoSansSC_700Bold.ttf"

f_reg = FontProperties(fname=FONT_REG)
f_med = FontProperties(fname=FONT_MED)
f_bold = FontProperties(fname=FONT_BOLD)

NAVY = "#1F3A4D"
TEAL = "#2E6F73"
GRAY = "#59656D"
LIGHT = "#EDF3F5"
LIGHT2 = "#F5F8F9"
BORDER = "#C9D6DC"

fig = plt.figure(figsize=(12, 8.6), dpi=260)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 12)
ax.set_ylim(0, 8.6)
ax.axis("off")
fig.patch.set_facecolor("white")

# Title
ax.text(0.52, 8.18, "分析流程：从语料构建到策略提炼",
        fontproperties=f_bold, fontsize=21, color=NAVY, va="center")
ax.text(0.52, 7.72, "三层递进：结构描写  →  语言实现  →  语境解释",
        fontproperties=f_reg, fontsize=11.5, color=TEAL, va="center")

steps = [
    ("01", "语料构建", "官网 About Us 主页面与子页面 → 清洗、元数据、页面类型 → 全量栏目语料 / 核心可比文本", "第3章"),
    ("02", "框架与标注", "24 个细类归并为 10 个核心语步 → AI 预标注 → 研究者逐篇审阅、修改、保存", "第3章"),
    ("03", "结构统计", "出现率 · 篇幅与占比 · 首次位置 · 开篇方式 → 600 个“文本 × 语步”记录", "第4章"),
    ("04", "语言分析", "分语步关键词 · 标准化频次 · G² / log2 / BH 校正 · 搭配与 KWIC · 语义组", "第5章"),
    ("05", "语境解释", "典型与边缘案例 → 跨文化话语分析 → CDA 文本 / 话语实践 / 社会实践", "第6章"),
    ("06", "策略提炼", "问题—策略—示例—适用边界 → 面向中国外语院系的话语策略建议库", "第6章"),
]

x_box, w_box, h_box = 2.05, 8.32, 0.84
top = 6.52
gap = 1.05

for i, (num, title, desc, chapter) in enumerate(steps):
    y = top - i * gap
    # main box
    ax.add_patch(FancyBboxPatch(
        (x_box, y), w_box, h_box,
        boxstyle="round,pad=0.015,rounding_size=0.07",
        facecolor="white", edgecolor=BORDER, linewidth=1.0, zorder=2))
    # left accent strip
    ax.add_patch(FancyBboxPatch(
        (x_box, y + 0.06), 0.075, h_box - 0.12,
        boxstyle="round,pad=0.005,rounding_size=0.03",
        facecolor=TEAL if i >= 2 else NAVY, edgecolor="none", zorder=3))
    # number circle
    ax.add_patch(Circle((x_box + 0.33, y + h_box / 2), 0.175,
                        facecolor=TEAL if i >= 2 else NAVY, edgecolor="none", zorder=4))
    ax.text(x_box + 0.33, y + h_box / 2 + 0.005, num,
            fontproperties=f_bold, fontsize=9.2, color="white",
            ha="center", va="center", zorder=5)
    # title and description
    ax.text(x_box + 0.62, y + 0.565, title,
            fontproperties=f_bold, fontsize=12.3, color=NAVY, va="center", zorder=5)
    ax.text(x_box + 0.62, y + 0.275, desc,
            fontproperties=f_reg, fontsize=9.3, color=GRAY, va="center", zorder=5)
    # chapter pill
    ax.add_patch(FancyBboxPatch(
        (10.52, y + 0.255), 0.92, 0.33,
        boxstyle="round,pad=0.01,rounding_size=0.09",
        facecolor=LIGHT, edgecolor="none", zorder=3))
    ax.text(10.98, y + 0.42, chapter,
            fontproperties=f_med, fontsize=8.6, color=TEAL,
            ha="center", va="center", zorder=4)
    # connector to chapter pill
    ax.plot([x_box + w_box, 10.52], [y + h_box / 2, y + h_box / 2],
            color=BORDER, linewidth=0.8, zorder=1)
    # arrow
    if i < len(steps) - 1:
        ax.add_patch(FancyArrowPatch(
            (x_box + w_box / 2, y - 0.015),
            (x_box + w_box / 2, y - gap + h_box + 0.015),
            arrowstyle="-|>", mutation_scale=10,
            linewidth=0.9, color=TEAL, zorder=1))

# Left layer brackets
layers = [
    ("文本准备", top + h_box, top - gap, 0.0),
    ("结构描写", top - 2 * gap + h_box, top - 2 * gap, 0.0),
    ("语言实现", top - 3 * gap + h_box, top - 3 * gap, 0.0),
    ("语境解释", top - 4 * gap + h_box, top - 5 * gap, 0.0),
]
for label, y_top, y_bottom, _ in layers:
    height = y_top - y_bottom
    ax.add_patch(FancyBboxPatch(
        (0.42, y_bottom), 1.28, height,
        boxstyle="round,pad=0.012,rounding_size=0.06",
        facecolor=LIGHT2, edgecolor="none", zorder=1))
    ax.text(1.06, (y_top + y_bottom) / 2, label,
            fontproperties=f_bold, fontsize=10.6, color=NAVY,
            ha="center", va="center", zorder=2, linespacing=1.5)

# Bottom quality band
ax.add_patch(FancyBboxPatch(
    (0.42, 0.31), 11.02, 0.50,
    boxstyle="round,pad=0.012,rounding_size=0.06",
    facecolor="#F3F6F7", edgecolor="none", zorder=1))
ax.text(0.62, 0.56,
        "质量控制：人工逐篇校订  ·  固定脚本计算  ·  600 组独立复算  ·  关键词回看原句  ·  核查来源集中度",
        fontproperties=f_reg, fontsize=9.4, color=NAVY, va="center")

ax.text(0.42, 0.13,
        "注：语步统计与关键词统计使用不同分母；复合标签可计入多个语步，但整篇独立词数只计一次。",
        fontproperties=f_reg, fontsize=7.9, color="#7A858C", va="center")

# Thin rule under subtitle
ax.plot([0.52, 11.48], [7.52, 7.52], color=BORDER, linewidth=0.8)

fig.savefig(FIG / "analysis_flow.png", dpi=260, facecolor="white", bbox_inches="tight", pad_inches=0.08)
fig.savefig(FIG / "analysis_flow.svg", facecolor="white", bbox_inches="tight", pad_inches=0.08)
plt.close(fig)
print("saved", FIG / "analysis_flow.png")
