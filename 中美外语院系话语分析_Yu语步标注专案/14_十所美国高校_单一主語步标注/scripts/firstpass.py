# -*- coding: utf-8 -*-
import sys, os, re, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import segment as S, rules as R

UP = '/tmp/arena-coding-uploads'
FILES = ['Boston University.txt', 'Brown University.txt', 'California Institute of Technology.txt',
         'Carnegie Mellon University.txt', 'Columbia University.txt', 'Cornell University.txt',
         'Duke University.txt', 'Georgia Institute of Technology.txt', 'Harvard University.txt',
         'Johns Hopkins University.txt']

def build():
    data = {}
    for f in FILES:
        raw = open(os.path.join(UP, f), encoding='utf-8-sig').read()
        units = S.segment(raw)
        # 全库重复短行 → 页脚/导航
        from collections import Counter
        cnt = Counter(re.sub(r'\s+', ' ', u).strip().lower() for u in units)
        labs = []
        for u in units:
            key = re.sub(r'\s+', ' ', u).strip().lower()
            if cnt[key] >= 5 and len(u.split()) <= 30:
                labs.append(('OTHER', 99, 'repeat'))
            else:
                labs.append(R.classify(u))
        data[f] = {'raw': raw, 'units': units, 'labels': [l for l, _, _ in labs], 'conf': labs}
    return data

if __name__ == '__main__':
    data = build()
    from collections import Counter
    for f, d in data.items():
        c = Counter(d['labels'])
        print(f'{f:40s}', ' '.join(f'{k}:{c.get(k,0)}' for k in [f'M{i:02d}' for i in range(1,11)]+['OTHER']))
    json.dump({f: {'units': d['units'], 'labels': d['labels'], 'conf': d['conf']} for f, d in data.items()},
              open('scripts/_pass1.json', 'w'), ensure_ascii=False)
