#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语步标注流水线（segment -> assemble -> qc）。

切分原则（对齐 07 号操作说明）：
  * 一个完整句 = 一个标注单元；
  * 一个内聚的「名片式人员卡片 / 地址联系块 / 名录列表块」= 一个标注单元（不拆成裸姓名）；
  * 不跨段合并，避免制造复合语步。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
RAW = os.path.join(ROOT, "原始语料")
OUT = os.path.join(ROOT, "标注结果")
SEG = os.path.join(BASE, "segments")
LAB = os.path.join(BASE, "labels")
SKEL = os.path.join(SEG, "skeleton.json")

ABBR = {
    "p", "r", "u.s", "u.k", "e.g", "i.e", "ph.d", "dr", "prof", "mr", "ms", "mrs",
    "st", "no", "jr", "sr", "vs", "inc", "ltd", "co", "univ", "dept", "pp", "vol", "fig",
    "approx", "ca", "cf", "al", "b.a", "m.a", "b.sc", "m.sc", "a.m", "p.m", "j", "w", "h",
    "hon", "pres", "gen", "col", "lt", "capt", "rev", "mt", "ft", "sq", "ave", "blvd", "rd",
}

CON_FIELD = re.compile(
    r"^(Tel|Telephone|Phone|Email|E-mail|E-Mail|Fax|Website|Web\s?site|Web|Address|Postcode|"
    r"Post\s?code|Postal\s?code|Zip|Zip\s?Code|Office|Office\s?Address|Office\s?Hour\w*|Contact|"
    r"Contact\s?number|Location|Mailing\s?Address|School\s?Address|Email\s?Address|URL)\b", re.I)
CARD_FIELD = re.compile(
    r"^(Title|Position|Job\s?Responsibility|Responsibilities|Responsibility|Division\s?of\s?work|"
    r"Duties|Tel|Telephone|Phone|Email|E-mail|Fax|Office|Office\s?Address|Director|Dean|Secretary|"
    r"Deputy|Associate|Professor|Lecturer|Head)\b", re.I)
BULLET = re.compile(r"^[-–•·*·]\s+|^\d+[.)]\s+")


def split_sentences(text):
    parts, buf = [], ""
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        buf += ch
        if ch in ".!?":
            j = i + 1
            while j < n and text[j] in "\"”’')]":
                buf += text[j]
                j += 1
            k = j
            if k >= n:
                parts.append(buf)
                buf, i = "", j
                continue
            if text[k] in " \t":
                m = k
                while m < n and text[m] in " \t":
                    m += 1
                nxt = text[m] if m < n else ""
                mw = re.search(r"([A-Za-z][A-Za-z.]*)$", buf.rstrip("\"”’')] "))
                pw = mw.group(1).lower().rstrip(".") if mw else ""
                if ch == "." and (pw in ABBR or (len(pw) == 1 and len(buf) > 2 and buf[-3].isupper())):
                    i = j
                    continue
                if nxt and (nxt.isupper() or nxt.isdigit() or nxt in "“\"'(["):
                    parts.append(buf)
                    parts_buf = ""
                    buf = ""
                    i = j
                    continue
            i = j
            continue
        i += 1
    if buf.strip():
        parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def is_card(lines):
    """名片式人员卡片 / 地址联系块：整体作为一个标注单元。"""
    if not (2 <= len(lines) <= 12):
        return False
    if max(len(x) for x in lines) > 260:
        return False
    has_con = any(CON_FIELD.match(x) for x in lines)
    if has_con and len(lines) <= 8:
        return True
    first = lines[0]
    if len(first) <= 45 and not first.endswith((".", "?", "!")) and len(first.split()) <= 5:
        if sum(1 for x in lines[1:] if CARD_FIELD.match(x)) >= 1:
            return True
    return False


def is_list_block(lines):
    if len(lines) >= 2 and sum(1 for x in lines if BULLET.match(x)) >= max(2, len(lines) * 0.6):
        return True
    return False


ROSTER_LINE = re.compile(
    r"^(Full\s+Professor|Associate\s+Professor|Assistant\s+Professor|Professor|Lecturer|Instructor|"
    r"Teaching\s+Staff|Research\s+Fellow|Name)\b.*[:：]?\s*\S", re.I)


def paragraphs(raw):
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = raw.lstrip("\ufeff")
    out = []
    for pa in re.split(r"\n\s*\n", raw):
        lines = [l.strip() for l in pa.split("\n") if l.strip()]
        if lines:
            out.append(lines)
    return out


def units_of(raw):
    """返回 [(unit_text, para_id)]；para_id 用于还原原文段落空行。"""
    items = []
    for pid, lines in enumerate(paragraphs(raw)):
        if is_card(lines) or is_list_block(lines):
            items.append(("\n".join(lines), pid))
            continue
        for l in lines:
            for u in split_sentences(l):
                items.append((u, pid))
    merged, i = [], 0
    while i < len(items):
        u, pid = items[i]
        if "\n" not in u and CON_FIELD.match(u) and len(u) < 160:
            j, group = i, []
            while (j < len(items) and "\n" not in items[j][0] and CON_FIELD.match(items[j][0])
                   and len(items[j][0]) < 160):
                group.append(items[j][0])
                j += 1
            if len(group) > 1:
                merged.append(("\n".join(group), items[j - 1][1]))
                i = j
                continue
        if "\n" not in u and ROSTER_LINE.match(u):
            j, group = i, []
            while j < len(items) and "\n" not in items[j][0] and ROSTER_LINE.match(items[j][0]):
                group.append(items[j][0])
                j += 1
            if len(group) > 1:
                merged.append(("\n".join(group), items[j - 1][1]))
                i = j
                continue
        merged.append((u, pid))
        i += 1
    return merged


def files():
    return sorted(f for f in os.listdir(RAW) if f.endswith(".txt"))


def segment():
    os.makedirs(SEG, exist_ok=True)
    os.makedirs(LAB, exist_ok=True)
    skel = {}
    for f in files():
        raw = open(os.path.join(RAW, f), encoding="utf-8").read()
        items = units_of(raw)
        units = [u for u, _ in items]
        skel[f] = {"units": units, "paras": [p for _, p in items]}
        stem = f[:-4]
        with open(os.path.join(SEG, stem + ".segments.tsv"), "w", encoding="utf-8") as fh:
            for gid, u in enumerate(units):
                fh.write(f"{gid}\t{u.replace(chr(10), ' ⏎ ')}\n")
        print(f"{stem}: units={len(units)}")
    json.dump(skel, open(SKEL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def read_labels(stem):
    labels, path = {}, os.path.join(LAB, stem + ".labels.tsv")
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        gid, lab = line.split("\t")[:2]
        labels[int(gid)] = lab.strip()
    return labels


def assemble():
    skel = json.load(open(SKEL, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    for f, rec in skel.items():
        stem = f[:-4]
        units, paras = rec["units"], rec["paras"]
        labels = read_labels(stem)
        lines = []
        for gid, u in enumerate(units):
            if gid not in labels:
                sys.exit(f"[缺失标签] {stem} 单元 {gid}: {u[:70]}")
            codes = labels[gid].split("+")
            o = "".join(f"<{c}>" for c in codes)
            c = "".join(f"</{k}>" for k in reversed(codes))
            lines.append(f"{o}{u}{c}")
            if gid + 1 == len(units) or paras[gid + 1] != paras[gid]:
                lines.append("")
        open(os.path.join(OUT, stem + ".txt"), "w", encoding="utf-8").write(
            "\n".join(lines).rstrip("\n") + "\n")
        print(f"写出 {stem}.txt  单元={len(units)}")


TAG_RE = re.compile(r"</?(M\d\d|OTHER)>")


def qc():
    """质检：单元级（非行级）统计 + 逐字保真 + XML 合法性。"""
    skel = json.load(open(SKEL, encoding="utf-8"))
    rows, tu = [], 0
    for f, rec in skel.items():
        stem = f[:-4]
        units = rec["units"]
        raw = open(os.path.join(RAW, f), encoding="utf-8").read()
        out = open(os.path.join(OUT, stem + ".txt"), encoding="utf-8").read()
        labels = read_labels(stem)
        verbatim = re.sub(r"\s", "", raw.lstrip("\ufeff")) == re.sub(r"\s", "", TAG_RE.sub("", out))
        # XML：包一层根节点，检查标签配对且无游离文本
        body = "<ROOT>\n" + out + "\n</ROOT>"
        opens = re.findall(r"<(M\d\d|OTHER)>", body)
        closes = re.findall(r"</(M\d\d|OTHER)>", body)
        stack, ok = [], True
        for m in re.finditer(r"<(/?)([A-Z0-9]+)>", body):
            closing, tag = m.group(1) == "/", m.group(2)
            if not closing:
                stack.append(tag)
            else:
                if not stack or stack[-1] != tag:
                    ok = False
                else:
                    stack.pop()
        ok = ok and stack == []
        # 每个单元必须标签包裹（标签在首尾）
        unit_ok = True
        for u in units:
            pat = re.escape(u)
            m = re.search(r"(?:<M\d\d>|<OTHER>)+" + pat + r"(?:</(?:M\d\d|OTHER)>)+", out)
            if not m:
                unit_ok = False
        illegal = set(opens) - {f"M{i:02d}" for i in range(1, 11)} - {"OTHER"}
        # 单语步率（缺标签/空标签视为不合格）
        single = sum(1 for i in range(len(units)) if len(labels[i].split("+")) == 1)
        words = sum(len(re.findall(r"[A-Za-z0-9’'\-]+", u)) for u in units)
        rows.append((stem, len(units), words, len(units) - single, single / len(units) * 100,
                     verbatim, ok and unit_ok and not illegal, len(opens) == len(units)))
        tu += len(units)
    print(f"{'文件':46s} 单元  词数  复合  单语步率  逐字保真  语法  标签数=单元数")
    ts = 0
    for stem, n, w, comp, rate, v, ok, cnt in rows:
        print(f"{stem:46s} {n:4d} {w:5d} {comp:4d}  {rate:6.2f}%  {str(v):>6s} {str(ok):>5s} {str(cnt):>6s}")
        ts += round(n * rate / 100)
    print(f"{'合计':46s} {tu:4d} {'':5s} {tu - ts:4d}  {ts / tu * 100:6.2f}%")
if __name__ == "__main__":
    {"segment": segment, "assemble": assemble, "qc": qc}[sys.argv[1] if len(sys.argv) > 1 else "segment"]()
