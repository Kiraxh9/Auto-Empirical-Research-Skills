# -*- coding: utf-8 -*-
"""生成 10 所美国高校语料的「一单元一主語步」标注文本 + 明细表 + 统计表 + 低置信度复核清单。"""
import os, re, sys, csv, json, math
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import segment as S, rules as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UP = '/tmp/arena-coding-uploads'
OUT = os.path.join(BASE, '标注后语料'); RAW = os.path.join(BASE, '原始语料')
os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)
FILES = ['Boston University.txt', 'Brown University.txt', 'California Institute of Technology.txt',
         'Carnegie Mellon University.txt', 'Columbia University.txt', 'Cornell University.txt',
         'Duke University.txt', 'Georgia Institute of Technology.txt', 'Harvard University.txt',
         'Johns Hopkins University.txt']
MOVES = [f'M{i:02d}' for i in range(1, 11)]

def norm(s):
    return re.sub(r'\s+', ' ', s).strip()

def main():
    detail, summary, review = [], [], []
    for f in FILES:
        raw = open(os.path.join(UP, f), encoding='utf-8-sig').read()
        open(os.path.join(RAW, f), 'w', encoding='utf-8').write(
            raw.replace('\r\n', '\n').replace('\r', '\n'))
        units = S.segment(raw)
        cnt = Counter(re.sub(r'\s+', ' ', u).strip().lower() for u in units)
        labs = []
        for u in units:
            key = re.sub(r'\s+', ' ', u).strip().lower()
            if cnt[key] >= 5 and len(u.split()) <= 30:
                labs.append(('OTHER', 2, 'repeat-block'))
            else:
                labs.append(R.classify(u))
        text = '\n\n'.join(f'<{lb}>{t}</{lb}>' for (lb, _, _), t in zip(labs, units))
        open(os.path.join(OUT, f), 'w', encoding='utf-8').write(text + '\n')

        # 明细
        for i, ((lb, c, why), t) in enumerate(zip(labs, units)):
            detail.append({'文件': f, '单元号': i + 1, '主語步': lb, '置信度': c,
                           '判定依据': why, '词数': len(t.split()), '文本': norm(t)})
            if c <= 1:
                review.append({'文件': f, '单元号': i + 1, '主語步': lb, '置信度': c,
                               '判定依据': why, '词数': len(t.split()), '文本': norm(t)})

        wc = {m: 0 for m in MOVES}; other = 0
        nc = {m: 0 for m in MOVES}; n_other = 0; conf_c = Counter()
        for lb, c, _ in labs:
            conf_c[c] += 1
        for (lb, c, _), t in zip(labs, units):
            w = len(t.split())
            if lb == 'OTHER':
                other += w; n_other += 1
            else:
                wc[lb] += w; nc[lb] += 1
        total = sum(wc.values()) + other
        valid = sum(wc.values())
        p = {m: (wc[m] / valid * 100 if valid else 0) for m in MOVES}
        ps = [v / 100 for v in p.values() if v > 0]
        H = -sum(x * math.log(x) for x in ps) if ps else 0
        summary.append({
            '文件': f, '原始总词数': total, '有效体裁词数': valid,
            '有效保留率(%)': round(valid / total * 100, 2), 'OTHER词数': other,
            'OTHER占比(%)': round(other / total * 100, 2),
            '单元数': len(units), '单元数_OTHER': n_other,
            '高置信单元数(≥2)': conf_c[2], '中置信单元数(1)': conf_c[1], '低置信单元数(0)': conf_c[0],
            '高置信词占比(%)': round(sum(len(t.split()) for (lb, c, _), t in zip(labs, units) if c == 2) / total * 100, 2),
            **{f'{m}_词数': wc[m] for m in MOVES},
            **{f'{m}_占比(%)': round(p[m], 2) for m in MOVES},
            '激活语步数': sum(1 for m in MOVES if wc[m] > 0),
            '香农熵H': round(H, 3), '均匀度J': round(H / math.log(10), 3),
            '复合语步单元数': 0, '复合语步率(%)': 0.0})

    # 合并池
    tot = {k: sum(float(r[k]) for r in summary) for k in ['原始总词数', '有效体裁词数', 'OTHER词数']}
    pool = {'文件': 'US_10_SUM（10所美国高校合并池）', '原始总词数': tot['原始总词数'],
            '有效体裁词数': tot['有效体裁词数'],
            '有效保留率(%)': round(tot['有效体裁词数'] / tot['原始总词数'] * 100, 2),
            'OTHER词数': tot['OTHER词数'],
            'OTHER占比(%)': round(tot['OTHER词数'] / tot['原始总词数'] * 100, 2),
            '单元数': sum(int(r['单元数']) for r in summary),
            '单元数_OTHER': sum(int(r['单元数_OTHER']) for r in summary),
            '高置信单元数(≥2)': sum(int(r['高置信单元数(≥2)']) for r in summary),
            '中置信单元数(1)': sum(int(r['中置信单元数(1)']) for r in summary),
            '低置信单元数(0)': sum(int(r['低置信单元数(0)']) for r in summary),
            '高置信词占比(%)': round(sum(r['高置信词占比(%)'] * r['原始总词数'] for r in summary) / tot['原始总词数'], 2)}
    for m in MOVES:
        w = sum(r[f'{m}_词数'] for r in summary)
        pool[f'{m}_词数'] = w
        pool[f'{m}_占比(%)'] = round(w / tot['有效体裁词数'] * 100, 2)
    ps = [pool[f'{m}_占比(%)'] / 100 for m in MOVES if pool[f'{m}_占比(%)'] > 0]
    H = -sum(x * math.log(x) for x in ps)
    pool.update({'激活语步数': sum(1 for m in MOVES if pool[f'{m}_词数'] > 0),
                 '香农熵H': round(H, 3), '均匀度J': round(H / math.log(10), 3),
                 '复合语步单元数': 0, '复合语步率(%)': 0.0})
    summary.append(pool)

    with open(os.path.join(BASE, '逐单元标注明细_10校.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['文件', '单元号', '主語步', '置信度', '判定依据', '词数', '文本'])
        w.writeheader(); w.writerows(detail)
    with open(os.path.join(BASE, '语步统计汇总_10校.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader(); w.writerows(summary)
    with open(os.path.join(BASE, '待复核清单_中低置信度.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['文件', '单元号', '主語步', '置信度', '判定依据', '词数', '文本'])
        w.writeheader(); w.writerows(review)
    json.dump({f: {'units': [d['文本'] for d in detail if d['文件'] == f]} for f in FILES},
              open(os.path.join(BASE, 'scripts', '_units_full.json'), 'w'), ensure_ascii=False)
    for r in summary:
        print(f"{r['文件'][:38]:38s} units={r['单元数']:5d} words={int(r['原始总词数']):6d} "
              f"valid={int(r['有效体裁词数']):6d} ({r['有效保留率(%)']}%) H={r['香农熵H']} J={r['均匀度J']}")

if __name__ == '__main__':
    main()
