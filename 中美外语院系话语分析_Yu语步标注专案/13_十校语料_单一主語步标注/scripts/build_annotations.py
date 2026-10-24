# -*- coding: utf-8 -*-
"""生成「一单元一語步」标注文本 + 明细表 + 统计表，并做逐词保真与标签合法性校验。"""
import json, os, re, sys, csv, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import labels_cn9, labels_beihang, move_units

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(BASE)
RAW_CN = os.path.join(PROJ, '中国大学')
RAW_DIR = os.path.join(BASE, '原始语料')
UP = '/tmp/arena-coding-uploads'
OUT_DIR = os.path.join(BASE, '标注后语料')
os.makedirs(RAW_DIR, exist_ok=True); os.makedirs(OUT_DIR, exist_ok=True)

MOVES = [f'M{i:02d}' for i in range(1, 11)] + ['OTHER']
MOVES = [f'M{i:02d}' for i in range(1, 11)]

def norm(s):
    return re.sub(r'\s+', ' ', s.replace('\r\n', '\n')).strip()

def build_units():
    """返回 {文件名: (原始原文, [(label, text)])}"""
    out = {}
    # --- 9 所既有语料：沿用原切分，仅替换为单一主語步 ---
    # 既有 9 校的单元序列：若缓存缺失，则从 ../中国大学/ 的嵌套标注重建
    cache = os.path.join(BASE, 'scripts', '_units.json')
    if os.path.exists(cache):
        prev = json.load(open(cache))
    else:
        import glob
        prev = {os.path.basename(p): [[c, t] for c, t in move_units.parse3(p)]
                for p in sorted(glob.glob(os.path.join(PROJ, '中国大学', '*.txt')))}
        json.dump(prev, open(cache, 'w'), ensure_ascii=False, indent=1)
    for fname in labels_cn9.CORRECTIONS:
        chains_text = prev[fname]
        corr = labels_cn9.CORRECTIONS[fname]
        units = []
        for i, (chain, text) in enumerate(chains_text):
            label = corr.get(i, chain[0])
            units.append((label, text))
        raw = open(os.path.join(UP, fname), encoding='utf-8-sig').read()
        out[fname] = (raw.replace('\r\n', '\n'), units)
    # --- Beihang：新切分 + 合并组 ---
    bh = json.load(open(os.path.join(BASE, 'scripts', '_beihang_units.json')))
    units = []
    for group, label in labels_beihang.GROUPS:
        units.append((label, '\n\n'.join(bh[i] for i in group)))
    raw = open(os.path.join(UP, 'Beihang University (former BUAA).txt'), encoding='utf-8-sig').read()
    out['Beihang University (former BUAA).txt'] = (raw.replace('\r\n', '\n'), units)
    return out

def main():
    data = build_units()
    detail, summary, problems = [], [], []
    for fname, (raw, units) in data.items():
        # 写出标注文本
        text = '\n\n'.join(f'<{lb}>{t.strip(chr(10))}</{lb}>' for lb, t in units)
        open(os.path.join(OUT_DIR, fname), 'w', encoding='utf-8').write(text + '\n')
        open(os.path.join(RAW_DIR, fname), 'w', encoding='utf-8').write(raw)
        # 校验 1：逐词零删改（剥离标签后与原始语料逐字符比对）
        if norm(re.sub(r'</?M\d\d>|</?OTHER>', '', text)) != norm(raw):
            import difflib
            a, b = norm(re.sub(r'</?M\d\d>|</?OTHER>', '', text)), norm(raw)
            sm = difflib.SequenceMatcher(None, a, b)
            d = [x for x in sm.get_opcodes() if x[0] != 'equal'][:3]
            problems.append((fname, 'FIDELITY', d))
        # 校验 2：单标签合法
        for i, (lb, t) in enumerate(units):
            if lb not in MOVES + ['OTHER']:
                problems.append((fname, 'BADLABEL', (i, lb)))
            if re.search(r'</?M\d\d>|</?OTHER>', t):
                problems.append((fname, 'RESIDUAL_TAG', i))
        # 明细
        for i, (lb, t) in enumerate(units):
            detail.append({'文件': fname, '单元号': i + 1, '主語步': lb,
                           '词数': len(t.split()), '文本': norm(t)})
        # 统计
        wc = {m: 0.0 for m in MOVES}
        other = 0.0
        for lb, t in units:
            w = len(t.split())
            if lb == 'OTHER':
                other += w
            else:
                wc[lb] += w
        total = sum(wc.values()) + other
        valid = sum(wc.values())
        p = {m: (wc[m] / valid * 100 if valid else 0.0) for m in MOVES}
        ps = [p[m] / 100 for m in MOVES if p[m] > 0]
        H = -sum(x * math.log(x) for x in ps) if ps else 0.0
        J = H / math.log(10) if valid else 0.0
        summary.append({'文件': fname, '原始总词数': round(total, 1), '有效体裁词数': round(valid, 1),
                        '有效保留率(%)': round(valid / total * 100, 2) if total else 0,
                        'OTHER词数': round(other, 1),
                        'OTHER占比(%)': round(other / total * 100, 2) if total else 0,
                        **{f'{m}_词数': round(wc[m], 1) for m in MOVES},
                        **{f'{m}_占比(%)': round(p[m], 2) for m in MOVES},
                        '激活语步数': sum(1 for m in MOVES if wc[m] > 0),
                        '香农熵H': round(H, 3), '均匀度J': round(J, 3),
                        '单元数': len(units),
                        '复合语步单元数': 0, '复合语步率(%)': 0.0})
    # 合并池行（词数加权）
    tot = {k: sum(float(r[k]) for r in summary) for k in ['原始总词数', '有效体裁词数', 'OTHER词数']}
    pool = {'文件': 'CN_10_SUM（10所中国高校合并池）', '原始总词数': round(tot['原始总词数'], 1),
            '有效体裁词数': round(tot['有效体裁词数'], 1),
            '有效保留率(%)': round(tot['有效体裁词数'] / tot['原始总词数'] * 100, 2),
            'OTHER词数': round(tot['OTHER词数'], 1),
            'OTHER占比(%)': round(tot['OTHER词数'] / tot['原始总词数'] * 100, 2)}
    for m in MOVES:
        w = sum(float(r[f'{m}_词数']) for r in summary)
        pool[f'{m}_词数'] = round(w, 1)
        pool[f'{m}_占比(%)'] = round(w / tot['有效体裁词数'] * 100, 2)
    ps = [pool[f'{m}_占比(%)'] / 100 for m in MOVES if pool[f'{m}_占比(%)'] > 0]
    H = -sum(x * math.log(x) for x in ps)
    pool.update({'激活语步数': sum(1 for m in MOVES if pool[f'{m}_词数'] > 0),
                 '香农熵H': round(H, 3), '均匀度J': round(H / math.log(10), 3),
                 '单元数': sum(int(r['单元数']) for r in summary),
                 '复合语步单元数': 0, '复合语步率(%)': 0.0})
    summary.append(pool)

    with open(os.path.join(BASE, '逐单元标注明细_10校.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['文件', '单元号', '主語步', '词数', '文本'])
        w.writeheader(); w.writerows(detail)
    with open(os.path.join(BASE, '语步统计汇总_10校.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader(); w.writerows(summary)
    print('PROBLEMS:', problems if problems else 'NONE (全部文件逐词保真 + 单标签合法)')
    for s in summary:
        print(s['文件'], s['原始总词数'], s['有效体裁词数'], f"{s['有效保留率(%)']}%",
              'OTHER', s['OTHER词数'], 'H', s['香农熵H'], 'J', s['均匀度J'],
              'moves', s['激活语步数'])

if __name__ == '__main__':
    main()
