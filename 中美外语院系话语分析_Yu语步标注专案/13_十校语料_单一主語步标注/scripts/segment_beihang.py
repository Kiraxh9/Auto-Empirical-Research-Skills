# -*- coding: utf-8 -*-
"""将 Beihang 原始 txt 切分为「单元」候选（不改变任何原始字符内容）。"""
import re, json, sys

src = sys.argv[1]
raw = open(src, encoding='utf-8-sig').read().replace('\r\n', '\n')
blocks = [b for b in raw.split('\n\n')]

ABBR = re.compile(r'\b(No|Prof|Dr|Mr|Mrs|Ms|St|vs|etc|e\.g|i\.e|U\.S|Ph\.D)\.$')
def split_sentences(text):
    text = text.strip()
    if not text:
        return []
    # 保护邮箱/网址中的点
    parts, buf = [], ''
    i = 0
    while i < len(text):
        buf += text[i]
        if text[i] in '.?!' :
            # 段末或后接空格+大写/引号 才切
            if i+1 >= len(text):
                parts.append(buf); buf = ''; i += 1; continue
            nxt = text[i+1:i+3]
            if re.match(r'[\s\n]', text[i+1]) and not ABBR.search(buf):
                parts.append(buf); buf = ''
        i += 1
    if buf.strip():
        parts.append(buf)
    return [p.strip() for p in parts if p.strip()]

units = []
for b in blocks:
    lines = [l for l in b.split('\n')]
    # 列表块（以 - 开头）整体作为一个单元
    if all(l.strip().startswith('-') or not l.strip() for l in lines if l.strip()):
        units.append('\n'.join(l for l in lines if l.strip()))
        continue
    nonempty = [l.strip() for l in lines if l.strip()]
    if len(nonempty) > 1:
        # 多行短块：可能是名录/课程/联系方式块 -> 整体保留
        short = all(len(l) < 90 for l in nonempty)
        if short and not any(re.search(r'[.?!]$', l) and len(l) > 60 for l in nonempty):
            units.append('\n'.join(nonempty))
            continue
        for l in nonempty:
            units.extend(split_sentences(l))
    else:
        for l in nonempty:
            units.extend(split_sentences(l))

json.dump(units, open('scripts/_beihang_units.json', 'w'), ensure_ascii=False, indent=1)
for i, u in enumerate(units):
    print(f'{i:3d} {" / ".join(u.split(chr(10)))[:160]}')
