# -*- coding: utf-8 -*-
"""美校语料单元切分：段落→句子/名录块，保持原文逐字符不变（仅规整行尾）。"""
import re

START = re.compile(r'[A-Z0-9"\u201c\'\u2018(\[-\u2013\u2014\u2022*]')
BULLET = re.compile(r'^[-•*·–—]\s+')
ABBR = {'dr', 'prof', 'mr', 'mrs', 'ms', 'st', 'jr', 'sr', 'no', 'vs', 'etc', 'e.g', 'i.e',
        'u.s', 'u.k', 'ph.d', 'fig', 'inc', 'ltd', 'co', 'dept', 'univ', 'approx', 'est'}

def _is_abbrev(prev):
    m = re.findall(r'([A-Za-z][A-Za-z.&]*)$', prev.strip())
    tail = m[-1] if m else ''
    t = tail.lower().rstrip('.')
    if t in ABBR:
        return True
    # 单个大写字母 = 人名缩写首字母（Daniel E. / Ruth L.）
    if re.fullmatch(r'[A-Z]', tail.rstrip('.')):
        return True
    if re.fullmatch(r'(?:[A-Za-z]\.)+[A-Za-z]?', tail.rstrip('.')) and len(tail) <= 6:
        return True
    return False

def split_sentences(text):
    """在 . ? ! 后（且非缩写/邮箱/网址/小数）断句；保留原字符。"""
    out, buf, i, n = [], '', 0, len(text)
    while i < n:
        ch = text[i]
        buf += ch
        i += 1
        if ch not in '.?!':
            continue
        nxt = text[i] if i < n else ''
        if nxt == '':
            break
        if nxt in '"\')]}”’':
            continue
        if not nxt.isspace():
            continue
        prev_word = buf[:-1]
        in_url = ('@' in buf[-40:]) or ('http' in buf[-80:]) or bool(re.search(r'\w\.\w', buf[-14:]))
        if in_url:
            continue
        if _is_abbrev(prev_word):
            continue
        # 下一句应疑似以大写/引号/数字/项目符号开头，否则视为句中停顿
        rest = text[i:].lstrip()
        if rest and not re.match(START, rest):
            continue
        out.append(buf)
        buf = ''
    if buf.strip():
        out.append(buf)
    return [s2.strip() for s2 in out if s2.strip()]

def segment(raw):
    raw = raw.replace('\r\n', '\n').replace('\r', '\n')
    blocks = re.split(r'\n[ \t]*\n', raw)
    units = []
    for b in blocks:
        lines = [l.strip() for l in b.split('\n') if l.strip()]
        if not lines:
            continue
        bullet = [l for l in lines if BULLET.match(l)]
        if bullet and len(bullet) >= len(lines) - 1:
            # 名录式短条目整体封装；内容式列表逐条切分
            if all(len(l.split()) <= 6 for l in lines):
                units.append('\n'.join(lines))
            else:
                for l in lines:
                    units.extend(split_sentences(l))
            continue
        if len(lines) > 1:
            short = all(len(l) <= 80 for l in lines)
            no_period = not any(re.search(r'[.!?]["”’)]?$', l) for l in lines)
            if short and no_period:
                units.append('\n'.join(lines))
                continue
        text = '\n'.join(lines)
        units.extend(split_sentences(text))
    return units
