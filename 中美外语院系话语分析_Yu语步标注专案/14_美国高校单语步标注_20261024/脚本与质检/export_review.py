#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出低置信度复核清单：判定路径为 fallback（弱兜底）且为实质句（≥7 词）的单元。"""
import csv, json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
skel = json.load(open(os.path.join(BASE, "segments", "skeleton.json"), encoding="utf-8"))
out = os.path.join(ROOT, "标注结果", "02_低置信度复核清单.csv")
rows = []
for f, rec in skel.items():
    stem = f[:-4]
    labels, paths = {}, {}
    for line in open(os.path.join(BASE, "labels", stem + ".labels.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        g, l = line.rstrip("\n").split("\t")[:2]
        labels[int(g)] = l
    for line in open(os.path.join(BASE, "labels", stem + ".paths.tsv"), encoding="utf-8"):
        g, p = line.rstrip("\n").split("\t")[:2]
        paths[int(g)] = p
    for i, u in enumerate(rec["units"]):
        n = len(re.findall(r"[A-Za-z0-9’'\-]+", u))
        if paths.get(i) == "fallback" and n >= 7:
            rows.append([stem, i, labels[i], n, u.replace("\n", " ⏎ ")])
with open(out, "w", encoding="utf-8-sig", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["高校", "单元编号", "当前标签", "词数", "原文单元"])
    wr.writerows(rows)
print(f"已写出 {out}（{len(rows)} 条待复核）")
