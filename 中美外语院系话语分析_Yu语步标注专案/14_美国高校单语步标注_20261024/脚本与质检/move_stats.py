#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按语步统计词数与单元数，输出分布矩阵 CSV + 控制台表格。"""
import csv
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
MOVES = [f"M{i:02d}" for i in range(1, 11)] + ["OTHER"]
CN = {"M01": "机构身份与治理", "M02": "历史沿革", "M03": "使命愿景", "M04": "学科价值与研究取向",
      "M05": "课程培养体系", "M06": "师资与支撑条件", "M07": "声誉与育人成效", "M08": "合作网络与公共服务",
      "M09": "欢迎与动员", "M10": "信息入口与规程", "OTHER": "网页残片"}


def load():
    skel = json.load(open(os.path.join(BASE, "segments", "skeleton.json"), encoding="utf-8"))
    rows = []
    for f, rec in skel.items():
        stem = f[:-4]
        labels = {}
        for line in open(os.path.join(BASE, "labels", stem + ".labels.tsv"), encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                gid, lab = line.rstrip("\n").split("\t")[:2]
                labels[int(gid)] = lab.strip()
        rows.append((stem, rec["units"], labels))
    return rows


def wc(s):
    return len(re.findall(r"[A-Za-z0-9’'\-]+", s))


def main():
    rows = load()
    table, tot_w, tot_u = [], {m: 0 for m in MOVES}, {m: 0 for m in MOVES}
    for stem, units, labels in rows:
        w = {m: 0 for m in MOVES}
        u = {m: 0 for m in MOVES}
        total = 0
        for gid, t in enumerate(units):
            n = wc(t)
            total += n
            for code in labels[gid].split("+"):
                w[code] += n
                u[code] += 1
        for m in MOVES:
            tot_w[m] += w[m]
            tot_u[m] += u[m]
        table.append((stem, len(units), total, w, u))
    out = os.path.join(ROOT, "标注结果", "00_10语步分布统计.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        wr = csv.writer(fh)
        head = ["高校", "标注单元数", "总词数", "有效话语词数(不含OTHER)", "OTHER词数"]
        for m in MOVES:
            head += [f"{m}词数", f"{m}词占比", f"{m}单元数"]
        wr.writerow(head)
        for stem, nu, tw, w, u in table:
            eff = tw - w["OTHER"]
            r = [stem, nu, tw, eff, w["OTHER"]]
            for m in MOVES:
                r += [w[m], f"{w[m] / eff * 100:.2f}%" if m != "OTHER" else "-", u[m]]
            wr.writerow(r)
        total_w = sum(t[1][2] for t in [(0, t) for t in table])
        total_w = sum(t[2] for t in table)
        total_u = sum(tot_u.values())
        r = ["合计", sum(t[1] for t in table), total_w, total_w - tot_w["OTHER"], tot_w["OTHER"]]
        for m in MOVES:
            r += [tot_w[m], f"{tot_w[m] / (total_w - tot_w['OTHER']) * 100:.2f}%" if m != "OTHER" else "-", tot_u[m]]
        wr.writerow(r)
    print(f"已写出 {out}\n")
    print(f"{'高校':38s}" + "".join(f"{m:>7s}" for m in MOVES if m != "OTHER") + f"{'有效词数':>9s}")
    for stem, nu, tw, w, u in table:
        eff = tw - w["OTHER"]
        print(f"{stem:38.38s}" + "".join(f"{w[m] / eff * 100:6.1f}%" for m in MOVES if m != "OTHER") + f"{eff:8d}")
    total_w = sum(t[2] for t in table)
    eff = total_w - tot_w["OTHER"]
    print(f"{'合计（词占比，不含OTHER）':36s}" + "".join(f"{tot_w[m] / eff * 100:6.1f}%" for m in MOVES if m != "OTHER") + f"{eff:8d}")
    total_u = sum(tot_u.values())
    print(f"{'合计（单元占比）':36s}" + "".join(f"{tot_u[m] / total_u * 100:6.1f}%" for m in MOVES) + f"{total_u:8d}")
    print("\n语步名称：" + "；".join(f"{m}={CN[m]}" for m in MOVES))


if __name__ == "__main__":
    main()
