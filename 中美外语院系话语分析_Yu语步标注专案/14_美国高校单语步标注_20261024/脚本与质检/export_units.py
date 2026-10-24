#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出单元级标注明细（便于人工复核与统计复算）。"""
import csv, json, os, re
BASE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(BASE)
skel = json.load(open(os.path.join(BASE, "segments", "skeleton.json"), encoding="utf-8"))
out = os.path.join(ROOT, "标注结果", "01_单元级标注明细.csv")
with open(out, "w", encoding="utf-8-sig", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["高校", "单元编号", "语步标签", "词数", "原文单元"])
    for f, rec in skel.items():
        stem = f[:-4]
        labels = {}
        for line in open(os.path.join(BASE, "labels", stem + ".labels.tsv"), encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                gid, lab = line.rstrip("\n").split("\t")[:2]
                labels[int(gid)] = lab.strip()
        for gid, u in enumerate(rec["units"]):
            wr.writerow([stem, gid, labels[gid], len(re.findall(r"[A-Za-z0-9’'\-]+", u)),
                         u.replace("\n", " ⏎ ")])
print("已写出", out)
