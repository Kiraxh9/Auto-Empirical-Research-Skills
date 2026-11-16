from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, Circle

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "开题汇报_一页速查.png"

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
LIGHT2 = "#F6F9FA"
BORDER = "#C9D6DC"

W, H = 8.27, 11.69
fig = plt.figure(figsize=(W, H), dpi=220)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
fig.patch.set_facecolor("white")

# Header
ax.text(0.55, 11.18, "开题汇报 · 速查", fontproperties=f_bold, fontsize=10.5, color=TEAL, va="center")
ax.text(0.55, 10.68, "论文框架与分析流程", fontproperties=f_bold, fontsize=24, color=NAVY, va="center")
ax.text(0.55, 10.23, "中美外语院系英文简介话语比较分析", fontproperties=f_reg, fontsize=10.3, color=GRAY, va="center")
ax.plot([0.55, 7.72], [10.02, 10.02], color=BORDER, linewidth=1.0)

# One-sentence band
ax.add_patch(FancyBboxPatch((0.55, 9.30), 7.17, 0.58,
                            boxstyle="round,pad=0.012,rounding_size=0.06",
                            facecolor=LIGHT, edgecolor="none"))
ax.text(0.72, 9.59,
        "一句话：60 个院系 × 10 个语步，沿“结构—语言—语境”三层，落到一个可操作的话语策略库。",
        fontproperties=f_med, fontsize=8.8, color=NAVY, va="center")

# Section titles
ax.text(0.55, 9.06, "论文框架｜七章", fontproperties=f_bold, fontsize=11.6, color=TEAL, va="center")
ax.text(4.34, 9.06, "分析流程｜六步", fontproperties=f_bold, fontsize=11.6, color=TEAL, va="center")

chapters = [
    ("01", "绪论", "问题、背景、概念、结构"),
    ("02", "文献与框架", "机构话语、体裁、CDA、三层框架"),
    ("03", "研究设计", "60 院系、10 语步、人机协作"),
    ("04", "语步分布", "出现率、篇幅、位置、开篇"),
    ("05", "语言实现", "教育理念、学科身份、国际化"),
    ("06", "语境与策略", "CDA 三维、社会语境、策略库"),
    ("07", "结论", "发现、贡献、局限、未来"),
]

steps = [
    ("01", "语料构建", "主/子页、清洗、全量/核心"),
    ("02", "框架标注", "24→10、AI 预标注、人工校订"),
    ("03", "结构统计", "600 组合、出现率、占比、位置"),
    ("04", "语言分析", "关键词、G²、搭配、KWIC"),
    ("05", "语境解释", "案例、跨文化、CDA"),
    ("06", "策略提炼", "问题—策略—示例—边界"),
]

y0, rh, gap = 8.25, 0.61, 0.16
for i, (num, title, desc) in enumerate(chapters):
    x, y = 0.55, y0 - i * (rh + gap)
    ax.add_patch(FancyBboxPatch((x, y), 3.38, rh,
                                boxstyle="round,pad=0.01,rounding_size=0.05",
                                facecolor="white", edgecolor=BORDER, linewidth=0.8))
    ax.add_patch(Circle((x + 0.24, y + rh / 2), 0.13, facecolor=NAVY, edgecolor="none"))
    ax.text(x + 0.24, y + rh / 2, num, fontproperties=f_bold, fontsize=7.2,
            color="white", ha="center", va="center")
    ax.text(x + 0.45, y + rh * 0.66, title, fontproperties=f_bold, fontsize=9.6,
            color=NAVY, va="center")
    ax.text(x + 0.45, y + rh * 0.29, desc, fontproperties=f_reg, fontsize=7.6,
            color=GRAY, va="center")

for i, (num, title, desc) in enumerate(steps):
    x, y = 4.34, y0 - i * (rh + gap)
    ax.add_patch(FancyBboxPatch((x, y), 3.38, rh,
                                boxstyle="round,pad=0.01,rounding_size=0.05",
                                facecolor="white", edgecolor=BORDER, linewidth=0.8))
    ax.add_patch(Circle((x + 0.24, y + rh / 2), 0.13, facecolor=TEAL, edgecolor="none"))
    ax.text(x + 0.24, y + rh / 2, num, fontproperties=f_bold, fontsize=7.2,
            color="white", ha="center", va="center")
    ax.text(x + 0.45, y + rh * 0.66, title, fontproperties=f_bold, fontsize=9.6,
            color=NAVY, va="center")
    ax.text(x + 0.45, y + rh * 0.29, desc, fontproperties=f_reg, fontsize=7.6,
            color=GRAY, va="center")

ax.text(4.34, 3.93,
        "注：第 3 步与第 4 步分母不同；复合标签不重复计入独立词数。",
        fontproperties=f_reg, fontsize=7.0, color="#7A858C", va="center")

# Key design cards
ax.text(0.55, 3.38, "三个关键设计", fontproperties=f_bold, fontsize=11.2, color=TEAL, va="center")
cards = [
    ("可比性", "功能对等，不按名称一一对应；\n统计单位是院系，不是网页。"),
    ("语步框架", "24 个细类归并为\n10 个核心语步，有手册、\n边界和试标注。"),
    ("人机协作", "AI 预标注，研究者逐篇定稿；\n固定脚本计算并独立复算。"),
]
card_w, card_h, card_y = 2.30, 1.18, 1.92
for i, (head, body) in enumerate(cards):
    x = 0.55 + i * (card_w + 0.135)
    ax.add_patch(FancyBboxPatch((x, card_y), card_w, card_h,
                                boxstyle="round,pad=0.012,rounding_size=0.06",
                                facecolor=LIGHT2, edgecolor="none"))
    ax.text(x + 0.16, card_y + card_h - 0.28, head, fontproperties=f_bold,
            fontsize=9.4, color=NAVY, va="center")
    ax.text(x + 0.16, card_y + 0.38, body, fontproperties=f_reg,
            fontsize=7.3, color=GRAY, va="center", linespacing=1.65)

# Questions to ask
ax.text(0.55, 1.55, "三个请教", fontproperties=f_bold, fontsize=11.2, color=TEAL, va="center")
ax.text(0.55, 1.18,
        "① 三个研究问题是否收得够紧？     ② 第 5 章四个主题是否再合并？     ③ 第 6 章如何避免文化归因？",
        fontproperties=f_med, fontsize=8.2, color=NAVY, va="center")

# Footer
ax.plot([0.55, 7.72], [0.78, 0.78], color=BORDER, linewidth=0.9)
ax.text(0.55, 0.52,
        "不评价办学水平  ·  不把统计显著当文化因果  ·  不把美国文本当标准",
        fontproperties=f_reg, fontsize=7.8, color=GRAY, va="center")

fig.savefig(OUT, dpi=220, facecolor="white", bbox_inches="tight", pad_inches=0.06)
plt.close(fig)
print("saved", OUT)
