# -*- coding: utf-8 -*-
"""质检：逐词保真 / 单标签合法性 / 标签配平 / 结构良构（& 需先转义，因原文 & 逐字符保留）。"""
import glob, os, re, sys
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = re.compile(r'</?(M\d\d|OTHER)>')
MOVE = re.compile(r'^<(M01|M02|M03|M04|M05|M06|M07|M08|M09|M10|OTHER)>(.*)</\1>$', re.S)

def norm(s):
    return re.sub(r'\s+', ' ', s).strip()

def escape(s):
    s = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', '&amp;', s)
    return s.replace('<', '&lt;').replace('>', '&gt;') if False else s

def main():
    rows, fails = [], []
    for p in sorted(glob.glob(os.path.join(BASE, '标注后语料', '*.txt'))):
        name = os.path.basename(p)
        raw = open(os.path.join(BASE, '原始语料', name), encoding='utf-8-sig').read()
        ann = open(p, encoding='utf-8').read()
        # 按标签位置解析单元（允许单元内部含空行，如地址块 / 名录块）
        units, stack, cur, i = [], [], [], 0
        for m in TAG.finditer(ann):
            if not m.group(0).startswith('</'):
                stack.append(m.group(1)); cur = [m.start()]
            else:
                assert stack and stack[-1] == m.group(1), (name, m.group(1))
                stack.pop()
                if not stack:
                    units.append(ann[cur[0]:m.end()])
        assert not stack, name
        # 1) 每单元必须单标签且标签配平
        bad = [u[:60] for u in units if len(TAG.findall(u)) != 2 or not MOVE.match(u.strip())]
        # 2) 逐字符保真（剥离标签后与原文比对）
        stripped = norm(TAG.sub('', ann))
        if stripped != norm(raw):
            fails.append((name, 'FIDELITY'))
        # 3) 结构良构（转义 & 后解析）
        try:
            ET.fromstring('<root>' + re.sub(r'&(?!(amp|lt|gt|quot|apos);)', '&amp;', ann) + '</root>')
            well = True
        except Exception as e:
            well = False
            fails.append((name, 'XML', str(e)))
        if bad:
            fails.append((name, 'UNIT', bad[:3]))
        rows.append((name, len(units), 'PASS' if not bad else 'FAIL', 'PASS' if well else 'FAIL',
                     'PASS' if stripped == norm(raw) else 'FAIL'))
    print(f'{"文件":52s} {"单元数":>6s} {"单标签":>6s} {"结构":>6s} {"保真":>6s}')
    for r in rows:
        print(f'{r[0]:52s} {r[1]:6d} {r[2]:>6s} {r[3]:>6s} {r[4]:>6s}')
    print('\n结论：', '全部通过' if not fails else fails)

if __name__ == '__main__':
    main()
