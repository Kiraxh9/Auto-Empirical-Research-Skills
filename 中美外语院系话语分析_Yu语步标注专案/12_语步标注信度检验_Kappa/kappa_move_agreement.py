#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语步标注 Kappa 一致性分析器
Move-annotation (M01-M10 + OTHER) inter-rater agreement -> SPSS-ready datasets
================================================================================
用途
----
对同一篇"院系简介"的两份 XML 标签语步标注文件（例如：AI 嵌套标注 vs. 标准扁平标注）
做 Cohen's Kappa 一致性检验，并导出可直接导入 SPSS 的表格文件（.csv / .xlsx / .sav）。

支持
----
* 扁平标签      : <M06>text</M06>
* 嵌套标签      : <M06><M07>text</M07></M06>   -> 外层=主语步, 内层=子语步
* <OTHER> 标签
* 三种一致性口径：
    (1) strict  严格：仅比较【外层/主语步】标签
    (2) lenient 宽松：标准标签 ∈ {外层, 内层} 任一即判为一致（多标签口径，仅报百分比一致率）
    (3) inner   内层：仅对两份文件都给出内层标签的单元比较（本工程标准标注无内层，故通常为空）
* 整体 Kappa（含 Fleiss-Cohen-Everitt 标准误、95%CI、Bootstrap 百分位 CI）
* 加权 Kappa（线性 / 二次，序数敏感性分析，慎用）
* 逐语步类别 Kappa（每个语步拆成 2x2 表）

用法
----
    python kappa_move_agreement.py A.txt B.txt -o 输出目录 --name "北京师范大学"
    # 多篇批量（Linux/macOS）：
    for f in 目录A/*.txt; do python kappa_move_agreement.py "$f" "目录B/$(basename "$f")" -o 输出; done

依赖：numpy（必需）；pandas + pyreadstat（导出 .sav，可选）；openpyxl（导出 .xlsx，可选）

作者：话语研究分析流水线   许可：MIT
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

import numpy as np

# ----------------------------------------------------------------------------
# 编码本：10 核心语步 + OTHER  (与 06_精炼10核心语步编码手册.csv 一致)
# ----------------------------------------------------------------------------
CATS = [f"M{i:02d}" for i in range(1, 11)] + ["OTHER"]
CAT_INDEX = {c: i for i, c in enumerate(CATS)}          # M01->0 ... OTHER->10
CAT_CODE = {c: i + 1 for i, c in enumerate(CATS)}       # 数值编码: M01=1 ... OTHER=11
CAT_NAME_ZH = {
    "M01": "界定机构身份、人员组成与组织治理",
    "M02": "追溯历史沿革与学脉敬意",
    "M03": "宣示使命愿景与公共价值立场",
    "M04": "阐释学科价值与学术研究取向",
    "M05": "介绍课程供给与教学培养体系",
    "M06": "展示师资力量与办学支撑条件",
    "M07": "证明办学声誉与育人发展成效",
    "M08": "展示合作网络与社会公共服务",
    "M09": "欢迎受众、引导行动与动员支持",
    "M10": "提供信息入口、办事规程与运行通告",
    "OTHER": "非命题网页残片与纯名录过滤项",
}
# 序数距离（仅用于加权 Kappa 的敏感性分析；OTHER 视为与一切语步"完全不一致"）
ORD_SCALE = {c: i for i, c in enumerate(CATS[:10])}

OPEN_RE = re.compile(r"^\s*((?:<[A-Za-z0-9]+>)+)(.*?)((?:</[A-Za-z0-9]+>)+)\s*$", re.S)
TAG_RE = re.compile(r"<(/?)([A-Za-z0-9]+)>")


# ----------------------------------------------------------------------------
# 1. 解析
# ----------------------------------------------------------------------------
class Seg:
    __slots__ = ("outer", "inner", "text", "raw")

    def __init__(self, outer, inner, text, raw):
        self.outer, self.inner, self.text, self.raw = outer, inner, text, raw


def parse_annotated_txt(path: Path) -> list[Seg]:
    """解析带 XML 语步标签的纯文本，返回按原文顺序排列的标注单元列表。"""
    raw = path.read_text(encoding="utf-8")
    # 按空行切块；块内可能有多行（本工程一般一行一段）
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
    segs: list[Seg] = []
    for blk in blocks:
        lines = [l.strip() for l in blk.split("\n") if l.strip()]
        for ln in lines:
            m = OPEN_RE.match(ln)
            if not m:
                continue  # 无标签的裸文本行（不应出现），跳过
            opens = TAG_RE.findall(m.group(1))
            labels = [t for slash, t in opens if not slash]
            text = m.group(2).strip()
            outer = labels[0] if len(labels) >= 1 else None
            inner = labels[1] if len(labels) >= 2 else None
            segs.append(Seg(norm_cat(outer), norm_cat(inner), text, ln))
    return segs


def norm_cat(c):
    if c is None:
        return None
    c = c.strip().upper()
    if re.fullmatch(r"M\d{1,2}", c):
        return "M%02d" % int(c[1:])
    return c


def norm_text(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("’", "'").replace("“", '"').replace("”", '"')).strip().lower()


# ----------------------------------------------------------------------------
# 2. 对齐
# ----------------------------------------------------------------------------
def align(a: list[Seg], b: list[Seg]):
    """按文本对齐两份标注。完全相同则按序对齐，否则用 difflib 做序列对齐。"""
    from difflib import SequenceMatcher

    ta = [norm_text(s.text) for s in a]
    tb = [norm_text(s.text) for s in b]
    if ta == tb:
        return [(i, i) for i in range(len(ta))], []

    sm = SequenceMatcher(None, ta, tb, autojunk=False)
    pairs, warns = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                pairs.append((i1 + k, j1 + k))
        else:
            na, nb = i2 - i1, j2 - j1
            for k in range(max(na, nb)):
                ia = i1 + k if k < na else None
                ib = j1 + k if k < nb else None
                if ia is None or ib is None:
                    warns.append(f"仅单侧存在的语段: A#{ia} / B#{ib}")
                    continue
                pairs.append((ia, ib))
                warns.append(f"文本不完全一致但已强制配对: A#{ia} <-> B#{ib}")
    return pairs, warns


# ----------------------------------------------------------------------------
# 3. 统计
# ----------------------------------------------------------------------------
def confusion_matrix(pairs_lab, cats=CATS):
    k = len(cats)
    M = np.zeros((k, k), dtype=float)
    for x, y in pairs_lab:
        if x in CAT_INDEX and y in CAT_INDEX:
            M[CAT_INDEX[x], CAT_INDEX[y]] += 1
    return M


def kappa_from_matrix(M):
    N = M.sum()
    if N == 0:
        return None
    Po = np.trace(M) / N
    rowp = M.sum(1) / N
    colp = M.sum(0) / N
    Pe = float((rowp * colp).sum())
    if abs(1 - Pe) < 1e-12:
        return dict(N=N, Po=Po, Pe=Pe, kappa=float("nan"), se=float("nan"),
                    lo=float("nan"), hi=float("nan"), z=float("nan"), p=float("nan"),
                    note="Pe=1，Kappa 不可计算")
    kappa = (Po - Pe) / (1 - Pe)
    # Fleiss-Cohen-Everitt (1969) 渐近方差
    p = M / N
    k_ = len(M)
    term1 = sum(p[i, i] * (1 - (rowp[i] + colp[i]) * (1 - kappa)) ** 2 for i in range(k_))
    term2 = sum((1 - kappa) ** 2 * p[i, j] * (colp[i] + rowp[j]) ** 2
                for i in range(k_) for j in range(k_) if i != j)
    term3 = (kappa - Pe * (1 - kappa)) ** 2
    var = (term1 + term2 - term3) / (N * (1 - Pe) ** 2)
    se = math.sqrt(max(var, 0.0))
    lo, hi = kappa - 1.96 * se, kappa + 1.96 * se
    z = kappa / se if se > 0 else float("nan")
    try:
        from math import erfc
        p_val = erfc(abs(z) / math.sqrt(2))
    except Exception:
        p_val = float("nan")
    return dict(N=int(N), Po=Po, Pe=Pe, kappa=kappa, se=se, lo=lo, hi=hi,
                z=z, p=p_val, note="")


def weighted_kappa(M, kind="quadratic"):
    """加权 Kappa（把 M01..M10 视为有序，OTHER 与其它类目间权重=1 即完全不一致）。"""
    k = len(M)
    w = np.ones((k, k))
    for i, ci in enumerate(CATS[:k]):
        for j, cj in enumerate(CATS[:k]):
            if i == j:
                w[i, j] = 0.0
            elif ci == "OTHER" or cj == "OTHER":
                w[i, j] = 1.0
            else:
                d = abs(ORD_SCALE[ci] - ORD_SCALE[cj])
                dmax = 9.0
                w[i, j] = (d / dmax) if kind == "linear" else (d / dmax) ** 2
    N = M.sum()
    if N == 0:
        return None
    rowp = M.sum(1) / N
    colp = M.sum(0) / N
    num = (w * M).sum() / N
    den = (w * np.outer(rowp, colp)).sum()
    if den == 0:
        return float("nan")
    return 1 - num / den


def bootstrap_ci(pairs_lab, n_boot=10000, seed=20261023):
    rng = np.random.default_rng(seed)
    arr = np.array(pairs_lab, dtype=object)
    n = len(arr)
    if n == 0:
        return (float("nan"), float("nan"))
    ks = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        M = confusion_matrix([tuple(arr[i]) for i in idx])
        r = kappa_from_matrix(M)
        if r and not math.isnan(r["kappa"]):
            ks.append(r["kappa"])
    if not ks:
        return (float("nan"), float("nan"))
    return (float(np.percentile(ks, 2.5)), float(np.percentile(ks, 97.5)))


def per_category_kappa(pairs_lab):
    out = []
    for c in CATS:
        a = [1 if x == c else 0 for x, y in pairs_lab]
        b = [1 if y == c else 0 for x, y in pairs_lab]
        na, nb = sum(a), sum(b)
        M = np.zeros((2, 2))
        for i, j in zip(a, b):
            M[i, j] += 1
        r = kappa_from_matrix(M)
        if na == 0 and nb == 0:
            out.append(dict(cat=c, name=CAT_NAME_ZH[c], n_A=0, n_B=0, agree=float("nan"),
                            Po=float("nan"), Pe=float("nan"), kappa=float("nan"),
                            note="双方均未使用该语步，Kappa 不可计算"))
            continue
        out.append(dict(cat=c, name=CAT_NAME_ZH[c], n_A=na, n_B=nb,
                        agree=int(M[0, 0] + M[1, 1]), Po=r["Po"], Pe=r["Pe"],
                        kappa=r["kappa"], note=r["note"] or ""))
    return out


def interpret(k):
    """Landis & Koch (1977) 基准（附 Krippendorff 建议的可接受下限）。"""
    if k is None or math.isnan(k):
        return "不可计算"
    if k < 0.00:
        return "差（低于偶然）"
    if k < 0.20:
        return "轻微 Slight"
    if k < 0.40:
        return "一般 Fair"
    if k < 0.60:
        return "中等 Moderate"
    if k < 0.80:
        return "高度 Substantial"
    if k <= 1.00:
        return "几乎完美 Almost perfect"
    return ""


# ----------------------------------------------------------------------------
# 4. 导出
# ----------------------------------------------------------------------------
def write_csv(path: Path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:   # BOM: SPSS/Excel 中文不乱码
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def write_xlsx(path: Path, sheets: "OrderedDict[str, tuple[list, list]]"):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    wb.remove(wb.active)
    head_fill = PatternFill("solid", fgColor="1F4E78")
    head_font = Font(color="FFFFFF", bold=True)
    for name, (header, rows) in sheets.items():
        ws = wb.create_sheet(name[:31])
        ws.append(header)
        for c in ws[1]:
            c.fill, c.font = head_fill, head_font
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for r in rows:
            ws.append(list(r))
        for col in range(1, len(header) + 1):
            L = get_column_letter(col)
            width = max([len(str(header[col - 1]))] +
                        [len(str(r[col - 1])) for r in rows[:200]] or [10])
            ws.column_dimensions[L].width = min(max(width * 1.6 + 2, 10), 60)
        ws.freeze_panes = "A2"
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def write_sav(path: Path, df_rows, header, var_labels=None, value_labels=None):
    import pandas as pd
    import pyreadstat
    df = pd.DataFrame(df_rows, columns=header)
    path.parent.mkdir(parents=True, exist_ok=True)
    pyreadstat.write_sav(df, str(path), column_labels=var_labels,
                         variable_value_labels=value_labels or None)


# ----------------------------------------------------------------------------
# 5. 主流程
# ----------------------------------------------------------------------------
def analyse(pair_name: str, fa: Path, fb: Path, outdir: Path,
            label_a="AI标注", label_b="标准标注", n_boot=10000, make_sav=True):
    A = parse_annotated_txt(fa)
    B = parse_annotated_txt(fb)
    pairs, warns = align(A, B)

    recs = []
    for n, (ia, ib) in enumerate(pairs, 1):
        sa, sb = A[ia], B[ib]
        strict = int(sa.outer == sb.outer)
        lenient = int(sb.outer in {sa.outer, sa.inner} or
                      (sa.outer is None and sb.outer is None))
        recs.append(dict(
            id=n,
            text=sa.text,
            a_outer=sa.outer, a_inner=sa.inner, a_inner_code=(CAT_CODE.get(sa.inner) if sa.inner else None),
            b_outer=sb.outer, b_inner=sb.inner,
            a_code=CAT_CODE.get(sa.outer), b_code=CAT_CODE.get(sb.outer),
            strict=strict, lenient=lenient,
        ))

    # ---- 主分析：严格（外层 vs 标准） ----
    strict_pairs = [(r["a_outer"], r["b_outer"]) for r in recs if r["a_outer"] and r["b_outer"]]
    M = confusion_matrix(strict_pairs)
    res = kappa_from_matrix(M)
    blo, bhi = bootstrap_ci(strict_pairs, n_boot=n_boot)
    res["boot_lo"], res["boot_hi"] = blo, bhi
    res["w_linear"] = weighted_kappa(M, "linear")
    res["w_quad"] = weighted_kappa(M, "quadratic")
    res["interpret"] = interpret(res["kappa"])

    # ---- 逐语步 ----
    per_cat = per_category_kappa(strict_pairs)

    # ---- 宽松口径 ----
    lenient_agree = sum(r["lenient"] for r in recs)
    lenient_po = lenient_agree / len(recs) if recs else float("nan")

    # ---- 内层（仅双方都有内层时） ----
    inner_pairs = [(r["a_inner"], r["b_inner"]) for r in recs if r["a_inner"] and r["b_inner"]]
    inner_res = kappa_from_matrix(confusion_matrix(inner_pairs)) if inner_pairs else None

    outdir.mkdir(parents=True, exist_ok=True)

    # ============ 表1：主数据（每单元一行）—— SPSS 直接读入做 CROSSTABS ============
    h1 = ["UnitID", "SegText", "RaterA_Outer", "RaterA_Outer_Code", "RaterA_Inner",
          "RaterA_Inner_Code", "RaterB_Standard", "RaterB_Code", "Agree_Strict", "Agree_Lenient"]
    r1 = [[r["id"], r["text"][:120], r["a_outer"], r["a_code"], r["a_inner"] or "",
           (r["a_inner_code"] if r["a_inner_code"] else None), r["b_outer"], r["b_code"], r["strict"], r["lenient"]]
          for r in recs]
    write_csv(outdir / "SPSS_01_主数据_每单元一行.csv", h1, r1)

    inv_code = {v: f"{k} {CAT_NAME_ZH[k]}" for k, v in CAT_CODE.items()}
    vl = {"Agree_Strict": {0: "不一致", 1: "一致"},
          "Agree_Lenient": {0: "不一致", 1: "一致"},
          "RaterA_Outer_Code": inv_code,
          "RaterB_Code": inv_code,
          "RaterA_Inner_Code": inv_code}
    cl = {"UnitID": "标注单元序号", "SegText": "语段文本（截断120字符）",
          "RaterA_Outer": f"{label_a}：主语步（嵌套外层）",
          "RaterA_Outer_Code": f"{label_a}：主语步数值编码",
          "RaterA_Inner": f"{label_a}：子语步（嵌套内层，空=无）",
          "RaterA_Inner_Code": f"{label_a}：子语步数值编码",
          "RaterB_Standard": f"{label_b}：语步", "RaterB_Code": f"{label_b}：语步数值编码",
          "Agree_Strict": "严格一致（外层==标准）",
          "Agree_Lenient": "宽松一致（标准 ∈ {外层,内层}）"}
    if make_sav:
        try:
            write_sav(outdir / "SPSS_01_主数据_每单元一行.sav", r1, h1, var_labels=cl, value_labels=vl)
        except Exception as e:  # pragma: no cover
            print(f"[warn] .sav 导出失败：{e}")

    # ============ 表2：A×B 频数交叉表（含 0 单元，保证方阵） ============
    # SPSS CROSSTABS 只在"行/列取值集合完全相同"时输出 Kappa；若某语步只被一方使用
    # （本例 OTHER 仅 A 使用），表格非方阵 -> Kappa 不计算。
    # 标准解法（UCLA/IBM 社区推荐）：给该"缺失类别"的对角格补一个极小权重 EPS，
    # 使该行与该列都出现在表中而对结果的影响 < 1e-5。
    EPS = 1e-4
    h2 = ["RaterA_Outer", "RaterB_Standard", "Count", "A_Code", "B_Code", "W_forKappa"]
    r2 = []
    for i, ca in enumerate(CATS):
        for j, cb in enumerate(CATS):
            cnt = int(M[i, j])
            # 仅当该类目在 A、B 两侧的合计不都为 0，但交叉对角格为 0 时才需补齐
            need_pad = (M[i, :].sum() + M[:, j].sum() > 0) and cnt == 0 and i == j
            r2.append([ca, cb, cnt, CAT_CODE[ca], CAT_CODE[cb],
                       float(cnt) if cnt > 0 else (EPS if need_pad else 0.0)])
    write_csv(outdir / "SPSS_02_频数加权表_AxB.csv", h2, r2)
    if make_sav:
        try:
            write_sav(outdir / "SPSS_02_频数加权表_AxB.sav", r2, h2,
                      var_labels={"RaterA_Outer": f"{label_a}：主语步",
                                  "RaterB_Standard": f"{label_b}：语步",
                                  "Count": "单元频数（原始，用于描述统计）",
                                  "A_Code": "A数值编码", "B_Code": "B数值编码",
                                  "W_forKappa": f"用于 Kappa 的权重（空对角格补 {EPS} 以保证方阵）"},
                      value_labels={"A_Code": inv_code, "B_Code": inv_code})
        except Exception as e:  # pragma: no cover
            print(f"[warn] .sav 导出失败：{e}")

    # ============ 表3：逐语步二分长表（SPLIT FILE 后逐类目算 Kappa） ============
    h3 = ["UnitID", "MoveCat", "A_Flag_Outer", "B_Flag", "W_forKappa"]
    r3 = []
    for r in recs:
        for c in CATS:
            r3.append([r["id"], c, int(r["a_outer"] == c), int(r["b_outer"] == c), 1.0])
    # 保证每个语步的 2x2 表都是方阵：缺失的水平补一行极小权重的"离对角"单元
    pad_id = 90000
    for c in CATS:
        rows = [x for x in r3 if x[1] == c]
        la = {x[2] for x in rows}
        lb = {x[3] for x in rows}
        for lvl in (0, 1):
            if lvl not in la:
                r3.append([pad_id, c, lvl, 0, EPS]); pad_id += 1
            if lvl not in lb:
                r3.append([pad_id, c, 0, lvl, EPS]); pad_id += 1
    write_csv(outdir / "SPSS_03_逐语步二分长表.csv", h3, r3)
    if make_sav:
        try:
            write_sav(outdir / "SPSS_03_逐语步二分长表.sav", r3, h3,
                      var_labels={"UnitID": "标注单元序号（>=90000 为补齐用的虚拟单元）",
                                  "MoveCat": "语步类别",
                                  "A_Flag_Outer": f"{label_a}是否标注为该语步（0/1）",
                                  "B_Flag": f"{label_b}是否标注为该语步（0/1）",
                                  "W_forKappa": f"用于 Kappa 的权重（补齐单元为 {EPS}）"},
                      value_labels={"A_Flag_Outer": {0: "否", 1: "是"}, "B_Flag": {0: "否", 1: "是"}})
        except Exception as e:  # pragma: no cover
            print(f"[warn] .sav 导出失败：{e}")

    # ============ 表4：预先算好的结果汇总（供核对 / 直接写论文） ============
    def f(x, n=4):
        return "" if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), n)

    h4 = ["指标", "数值", "说明"]
    r4 = [
        ["配对单元数 N", res["N"], "两份文件成功对齐的标注单元数"],
        ["观察到的一致率 Po", f(res["Po"]), "对角线单元数 / N"],
        ["期望一致率 Pe", f(res["Pe"]), "Σ(行边际×列边际) / N²"],
        ["Cohen's Kappa", f(res["kappa"]), "(Po-Pe)/(1-Pe)"],
        ["标准误 SE (Fleiss-Cohen-Everitt)", f(res["se"]), "SPSS CROSSTABS 报告的 ASE 即此值"],
        ["Kappa 95%CI 下限 (正态近似)", f(res["lo"]), "κ − 1.96·SE"],
        ["Kappa 95%CI 上限 (正态近似)", f(res["hi"]), "κ + 1.96·SE"],
        [f"Kappa 95%CI 下限 (Bootstrap {n_boot}次)", f(res["boot_lo"]), "百分位法，小样本更稳健"],
        [f"Kappa 95%CI 上限 (Bootstrap {n_boot}次)", f(res["boot_hi"]), "百分位法，小样本更稳健"],
        ["z 值", f(res["z"]), "κ / SE"],
        ["p 值 (双侧)", f(res["p"], 6), "H0: Kappa = 0"],
        ["一致性强度判读", res["interpret"], "Landis & Koch (1977)"],
        ["加权 Kappa（线性）", f(res["w_linear"]), "敏感性分析：语步序数假设下（慎用）"],
        ["加权 Kappa（二次）", f(res["w_quad"]), "敏感性分析：语步序数假设下（慎用）"],
        ["宽松口径一致单元数", lenient_agree, f"标准语步 ∈ {label_a}的{{外层,内层}}集合"],
        ["宽松口径一致率", f(lenient_po), "多标签口径，Kappa 不适用，仅报百分比"],
    ]
    if inner_res:
        r4.append(["内层子语步 Kappa", f(inner_res["kappa"]), f"N={inner_res['N']}（仅双方均有内层的单元）"])
    write_csv(outdir / "SPSS_04_Kappa结果汇总.csv", h4, r4)

    # 逐语步结果表
    h5 = ["MoveCat", "MoveName_ZH", "N_A", "N_B", "AgreeCells", "Po", "Pe", "Kappa", "Note"]
    r5 = [[d["cat"], d["name"], d["n_A"], d["n_B"],
           "" if isinstance(d["agree"], float) else d["agree"],
           f(d["Po"]), f(d["Pe"]), f(d["kappa"]), d["note"]] for d in per_cat]
    write_csv(outdir / "SPSS_05_逐语步Kappa.csv", h5, r5)

    # ============ 混淆矩阵（人读） ============
    h6 = ["A\\B"] + CATS + ["行合计"]
    r6 = []
    for i, ca in enumerate(CATS):
        r6.append([ca] + [int(M[i, j]) for j in range(len(CATS))] + [int(M[i].sum())])
    r6.append(["列合计"] + [int(M[:, j].sum()) for j in range(len(CATS))] + [int(M.sum())])
    write_csv(outdir / "SPSS_06_混淆矩阵.csv", h6, r6)

    # ============ XLSX 汇总包 ============
    sheets = OrderedDict()
    sheets["00_变量与编码说明"] = (
        ["SPSS变量名", "中文标签", "取值/编码", "说明"],
        [["UnitID", "标注单元序号", "1..N", "两份文件按语段文本对齐后的序号"],
         ["SegText", "语段文本", "字符串（截断120字符）", "用于人工核查配对是否正确"],
         ["RaterA_Outer", f"{label_a}：主语步", "M01..M10, OTHER", "嵌套标签的最外层；无嵌套时即唯一标签"],
         ["RaterA_Outer_Code", f"{label_a}：主语步数值编码", "1..11", "M01=1 … M10=10, OTHER=11"],
         ["RaterA_Inner", f"{label_a}：子语步", "M01..M10, OTHER, 空", "嵌套标签的内层；无嵌套时为空"],
         ["RaterA_Inner_Code", f"{label_a}：子语步数值编码", "1..11 / 空", "同上"],
         ["RaterB_Standard", f"{label_b}：语步", "M01..M10, OTHER", "扁平标注，每个单元仅一个标签"],
         ["RaterB_Code", f"{label_b}：语步数值编码", "1..11", "同上"],
         ["Agree_Strict", "严格一致", "0=不一致, 1=一致", "RaterA_Outer == RaterB_Standard"],
         ["Agree_Lenient", "宽松一致", "0=不一致, 1=一致", "RaterB_Standard ∈ {A外层, A内层}"],
         ["Count", "单元频数", "≥0", "仅用于表2；原始频数，用于描述/核对"],
         ["W_forKappa", "Kappa 用权重", "Count 或 0.0001", "仅用于表2；缺失类别对角格补 1e-4，保证 CROSSTABS 成方阵 -> 必须 WEIGHT BY W_forKappa 再算 Kappa"],
         ["MoveCat", "语步类别", "M01..M10, OTHER", "仅用于表3（逐语步二分长表）"],
         ["A_Flag_Outer / B_Flag", "是否标注为该语步", "0=否, 1=是", "仅用于表3，配合 SPLIT FILE 求逐类目 Kappa"]]
    )
    sheets["01_主数据"] = (h1, r1)
    sheets["02_频数加权表"] = (h2, r2)
    sheets["03_逐语步二分长表"] = (h3, r3)
    sheets["04_Kappa结果汇总"] = (h4, r4)
    sheets["05_逐语步Kappa"] = (h5, r5)
    sheets["06_混淆矩阵"] = (h6, r6)
    sheets["07_不一致明细"] = (
        ["UnitID", "SegText", "A_外层", "A_内层", "B_标准", "严格一致", "宽松一致"],
        [[r["id"], r["text"][:200], r["a_outer"], r["a_inner"] or "", r["b_outer"],
          r["strict"], r["lenient"]] for r in recs if r["strict"] == 0])
    sheets["08_语步编码本"] = (
        ["语步代码", "中文名称", "数值编码"],
        [[c, CAT_NAME_ZH[c], CAT_CODE[c]] for c in CATS])
    write_xlsx(outdir / "语步Kappa_SPSS数据包.xlsx", sheets)

    # ============ 机器可读 ============
    (outdir / "_result.json").write_text(json.dumps(
        dict(pair=pair_name, N=res["N"], Po=res["Po"], Pe=res["Pe"], kappa=res["kappa"],
             se=res["se"], ci=[res["lo"], res["hi"]], boot_ci=[res["boot_lo"], res["boot_hi"]],
             p=res["p"], interpret=res["interpret"], w_linear=res["w_linear"],
             w_quad=res["w_quad"], lenient_po=lenient_po,
             per_category=per_cat, warnings=warns),
        ensure_ascii=False, indent=2), encoding="utf-8")

    return res, per_cat, recs, warns


def main(argv=None):
    ap = argparse.ArgumentParser(description="语步标注 Cohen's Kappa 一致性分析（导出 SPSS 数据表）")
    ap.add_argument("file_a", nargs="?", help="标注者A文件（可含嵌套标签）")
    ap.add_argument("file_b", nargs="?", help="标注者B文件（标准/对照标注）")
    ap.add_argument("-o", "--outdir", default="./kappa_out", help="输出目录")
    ap.add_argument("--name", default="语步标注配对", help="配对名称（用于报告标题）")
    ap.add_argument("--label-a", default="AI标注", help="标注者A名称")
    ap.add_argument("--label-b", default="标准标注", help="标注者B名称")
    ap.add_argument("--n-boot", type=int, default=10000, help="Bootstrap 重抽样次数")
    ap.add_argument("--no-sav", action="store_true", help="不导出 .sav 文件")
    args = ap.parse_args(argv)

    if not args.file_a or not args.file_b:
        ap.error("需要提供两份标注文件路径")

    res, per_cat, recs, warns = analyse(
        args.name, Path(args.file_a), Path(args.file_b), Path(args.outdir),
        label_a=args.label_a, label_b=args.label_b, n_boot=args.n_boot,
        make_sav=not args.no_sav)

    print("=" * 68)
    print(f"  {args.name}  |  {args.label_a}  vs  {args.label_b}")
    print("=" * 68)
    print(f"  N = {res['N']}")
    print(f"  Po = {res['Po']:.4f}   Pe = {res['Pe']:.4f}")
    print(f"  Cohen's Kappa = {res['kappa']:.4f}   SE = {res['se']:.4f}")
    print(f"  95%CI (正态)   = [{res['lo']:.4f}, {res['hi']:.4f}]")
    print(f"  95%CI (Bootstrap) = [{res['boot_lo']:.4f}, {res['boot_hi']:.4f}]")
    print(f"  z = {res['z']:.3f}   p = {res['p']:.6f}   -> {res['interpret']}")
    print(f"  加权Kappa: 线性={res['w_linear']:.4f}  二次={res['w_quad']:.4f}")
    print("-" * 68)
    print("  逐语步 Kappa：")
    for d in per_cat:
        kv = "  n/a" if (isinstance(d['kappa'], float) and math.isnan(d['kappa'])) else f"{d['kappa']:7.4f}"
        print(f"    {d['cat']}  nA={d['n_A']:2d} nB={d['n_B']:2d}  kappa={kv}   {d['name']}")
    if warns:
        print("-" * 68)
        for w in warns:
            print("  [对齐警示]", w)
    print("=" * 68)
    print(f"  输出目录：{Path(args.outdir).resolve()}")


if __name__ == "__main__":
    main()
