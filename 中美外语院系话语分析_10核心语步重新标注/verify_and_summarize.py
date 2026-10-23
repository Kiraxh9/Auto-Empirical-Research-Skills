#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10 核心语步重新标注 —— 全量保真度核验与语步分布统计脚本
================================================================
核验标准：
1. 原文逐词逐字符逐标点 100.00% 零删改保真 (raw.split() == stripped.split())
2. 100% 合法 XML 标签语法树（仅限 M01-M10 扁平或双层嵌套、以及独立 OTHER）
3. 100% 兼容 kappa_move_agreement.py 单行单元解析器（零跳过行、零丢词）
4. 按 Yu (2023) 复合语步等权分摊口径（双语步各计 0.5 词数与 0.5 单元）输出分布统计表
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from collections import Counter
from pathlib import Path

MOVES = [f"M{i:02d}" for i in range(1, 11)]
ALL_CATS = MOVES + ["OTHER"]

LINE_RE = re.compile(
    r"^<(M0[1-9]|M10|OTHER)>(?:<(M0[1-9]|M10)>)?([^<>]+?)(?:</(M0[1-9]|M10)>)?<\/(M0[1-9]|M10|OTHER)>$"
)


def verify_and_stat_file(ann_path: Path, raw_path: Path | None = None) -> dict:
    ann_text = ann_path.read_text(encoding="utf-8")
    non_empty_lines = [ln for ln in ann_text.splitlines() if ln.strip()]

    move_words = {c: 0.0 for c in ALL_CATS}
    move_units = {c: 0.0 for c in ALL_CATS}
    primary_units = Counter()
    combined_count = 0
    extracted_tokens: list[str] = []

    for idx, ln in enumerate(non_empty_lines, 1):
        m = LINE_RE.match(ln)
        if not m:
            raise ValueError(f"[{ann_path.name}:L{idx}] 非法标签格式: {ln[:100]!r}")
        o1, i1, body, i2, o2 = m.groups()
        if o1 != o2:
            raise ValueError(f"[{ann_path.name}:L{idx}] 外层开闭标签不匹配: <{o1}> vs </{o2}>")
        if i1 != i2:
            raise ValueError(f"[{ann_path.name}:L{idx}] 内层开闭标签不匹配: <{i1}> vs </{i2}>")
        if i1 is not None:
            if o1 == "OTHER" or i1 == "OTHER":
                raise ValueError(f"[{ann_path.name}:L{idx}] OTHER 不可与其他语步嵌套")
            if o1 == i1:
                raise ValueError(f"[{ann_path.name}:L{idx}] 内外层语步重复: <{o1}><{i1}>")

        tokens = body.split()
        if not tokens:
            raise ValueError(f"[{ann_path.name}:L{idx}] 空文本单元")
        extracted_tokens.extend(tokens)
        w = float(len(tokens))

        primary_units[o1] += 1
        if i1 is None:
            move_words[o1] += w
            move_units[o1] += 1.0
        else:
            combined_count += 1
            move_words[o1] += w / 2.0
            move_words[i1] += w / 2.0
            move_units[o1] += 0.5
            move_units[i1] += 0.5

    if raw_path is not None and raw_path.exists():
        raw_tokens = raw_path.read_text(encoding="utf-8").split()
        if raw_tokens != extracted_tokens:
            # Find first mismatch for clear debugging
            for k, (rt, et) in enumerate(zip(raw_tokens, extracted_tokens)):
                if rt != et:
                    raise ValueError(
                        f"[{ann_path.name}] 第 {k+1} 个词与原文不一致: raw={rt!r} vs ann={et!r}"
                    )
            raise ValueError(
                f"[{ann_path.name}] 总词数不一致: raw={len(raw_tokens)} vs ann={len(extracted_tokens)}"
            )

    total_words = sum(move_words.values())
    other_words = move_words["OTHER"]
    effective_words = total_words - other_words
    retention_pct = (effective_words / total_words * 100.0) if total_words > 0 else 0.0

    # Shannon evenness J across the 10 core moves (word-based)
    probs = [move_words[m] / effective_words for m in MOVES if move_words[m] > 0 and effective_words > 0]
    h = -sum(p * math.log(p) for p in probs) if probs else 0.0
    j_evenness = h / math.log(10) if probs else 0.0

    return {
        "university": ann_path.stem,
        "filename": ann_path.name,
        "total_units": len(non_empty_lines),
        "combined_units": combined_count,
        "effective_units": int(len(non_empty_lines) - move_units["OTHER"]),
        "total_words": total_words,
        "effective_words": effective_words,
        "other_words": other_words,
        "retention_pct": retention_pct,
        "shannon_J": j_evenness,
        "move_words": move_words,
        "move_units": move_units,
        "primary_units": primary_units,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="核验 10 核心语步标注文件并生成汇总 CSV")
    ap.add_argument(
        "--ann-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "标注语料",
        help="标注后 .txt 目录",
    )
    ap.add_argument(
        "--raw-dir",
        type=Path,
        default=None,
        help="可选：原始 preprocessed .txt 目录（用于 100% 逐词比对）",
    )
    ap.add_argument(
        "--out-csv",
        type=Path,
        default=Path(__file__).resolve().parent / "10校重新标注_10核心语步分布统计汇总表.csv",
        help="输出统计汇总 CSV 路径",
    )
    args = ap.parse_args()

    ann_files = sorted(args.ann_dir.glob("*.txt"))
    if not ann_files:
        print(f"未找到标注文件: {args.ann_dir}", file=sys.stderr)
        return 1

    rows = []
    for p in ann_files:
        raw_p = (args.raw_dir / p.name) if args.raw_dir else None
        st = verify_and_stat_file(p, raw_p)
        rows.append(st)
        print(
            f"[PASS] {st['filename']}: "
            f"units={st['total_units']} (combined={st['combined_units']}), "
            f"words={int(st['total_words'])}, "
            f"effective={st['effective_words']:.1f} ({st['retention_pct']:.2f}%), "
            f"J={st['shannon_J']:.3f}"
        )

    # Write summary CSV
    headers = [
        "高校英文名称",
        "总标注单元数",
        "有效话语单元数",
        "复合语步单元数",
        "总词数",
        "有效话语词数",
        "OTHER过滤词数",
        "有效词保留率(%)",
        "香农均匀度J",
    ]
    for m in MOVES:
        headers.append(f"{m}_词数")
        headers.append(f"{m}_占比(%)")

    with args.out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)

        tot_units = sum(r["total_units"] for r in rows)
        tot_eff_units = sum(r["effective_units"] for r in rows)
        tot_comb = sum(r["combined_units"] for r in rows)
        tot_words = sum(r["total_words"] for r in rows)
        tot_eff_words = sum(r["effective_words"] for r in rows)
        tot_other_words = sum(r["other_words"] for r in rows)
        pool_move_words = {m: sum(r["move_words"][m] for r in rows) for m in MOVES}

        for r in rows:
            eff = r["effective_words"]
            row_out = [
                r["university"],
                r["total_units"],
                r["effective_units"],
                r["combined_units"],
                f"{r['total_words']:.1f}",
                f"{eff:.1f}",
                f"{r['other_words']:.1f}",
                f"{r['retention_pct']:.2f}",
                f"{r['shannon_J']:.4f}",
            ]
            for m in MOVES:
                mw = r["move_words"][m]
                pct = (mw / eff * 100.0) if eff > 0 else 0.0
                row_out.extend([f"{mw:.1f}", f"{pct:.2f}"])
            w.writerow(row_out)

        # Pooled row
        pool_probs = [pool_move_words[m] / tot_eff_words for m in MOVES if pool_move_words[m] > 0]
        pool_j = (-sum(p * math.log(p) for p in pool_probs)) / math.log(10) if pool_probs else 0.0
        pool_row = [
            f"全部{len(rows)}所高校合并池 (Total Pool)",
            tot_units,
            tot_eff_units,
            tot_comb,
            f"{tot_words:.1f}",
            f"{tot_eff_words:.1f}",
            f"{tot_other_words:.1f}",
            f"{(tot_eff_words / tot_words * 100.0):.2f}",
            f"{pool_j:.4f}",
        ]
        for m in MOVES:
            mw = pool_move_words[m]
            pct = (mw / tot_eff_words * 100.0) if tot_eff_words > 0 else 0.0
            pool_row.extend([f"{mw:.1f}", f"{pct:.2f}"])
        w.writerow(pool_row)

    print(f"\n汇总统计已写入: {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
