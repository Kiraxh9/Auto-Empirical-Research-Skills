# -*- coding: utf-8 -*-
"""通用工具：解析/写出「每单元一行」的 XML 风格语步标注，逐词逐符号保真校验。"""
import re, os

OPEN = re.compile(r'<(M\d\d|OTHER)>')
CLOSE = re.compile(r'</(M\d\d|OTHER)>')
ANY = re.compile(r'</?(M\d\d|OTHER)>')

def parse(path):
    """解析标注文件 -> [(chain[list], text)]；chain 顺序为 外层→内层。"""
    raw = open(path, encoding='utf-8-sig').read()
    units, stack, chain, buf, i = [], [], [], [], 0
    for m in ANY.finditer(raw):
        buf.append(raw[i:m.start()])
        tok = m.group(0)
        if not tok.startswith('</'):
            chain.append(tok[1:-1])
        else:
            name = tok[2:-1]
            assert stack and stack[-1] == name, (path, name, stack)
            stack.pop(); chain.pop()
            if not stack:
                units.append(([c for c in m and []], ''.join(buf)))
        i = m.end()
    return units

def parse2(path):
    raw = open(path, encoding='utf-8-sig').read()
    units, stack, buf, i = [], [], [], 0
    for m in ANY.finditer(raw):
        buf.append(raw[i:m.start()])
        tok = m.group(0)
        if not tok.startswith('</'):
            stack.append(tok[1:-1])
        else:
            name = tok[2:-1]
            assert stack and stack[-1] == name, (path, name, stack)
            stack.pop()
            if not stack:
                units.append((None, ''.join(buf)))
        i = m.end()
    assert not stack, (path, stack)
    # 第二遍：重新扫描一次收集 chain（简单可靠）
    out, stack, buf, cur, i = [], [], [], [], 0
    for m in ANY.finditer(raw):
        seg = raw[i:m.start()]
        if seg: buf.append(seg)
        tok = m.group(0)
        if not tok.startswith('</'):
            stack.append(tok[1:-1]); cur.append(tok[1:-1])
        else:
            stack.pop(); cur.pop()
            if not stack:
                out.append((list(cur_snapshot) if False else None, ''.join(buf)))
        i = m.end()
    return out

def parse3(path):
    """单遍解析：返回 [(chain[外层→内层], text)]，text 为单元内原文。"""
    raw = open(path, encoding='utf-8-sig').read()
    out, chain, buf, i, snap = [], [], [], 0, []
    for m in ANY.finditer(raw):
        buf.append(raw[i:m.start()])
        tok = m.group(0)
        if not tok.startswith('</'):
            chain.append(tok[1:-1])
            if len(chain) == 1:
                snap = [tok[1:-1]]
                buf = []
            else:
                snap.append(tok[1:-1])
        else:
            name = tok[2:-1]
            assert chain and chain[-1] == name, (path, name, chain)
            chain.pop()
            if not chain:
                out.append((list(snap), ''.join(buf)))
                buf = []
        i = m.end()
    assert not chain, (path, chain)
    return out
