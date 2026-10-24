# -*- coding: utf-8 -*-
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules as R, gold
dev = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_dev.json')))
ok = 0
from collections import Counter
conf = Counter()
wrong = []
for (f, i, pred_old, u), g in zip(dev, gold.GOLD):
    lab, c, why = R.classify(u)
    conf[str(c)] += 1
    if lab == g:
        ok += 1
    else:
        wrong.append((g, lab, why, ' / '.join(u.split('\n'))[:110]))
print(f'accuracy {ok}/{len(dev)} = {ok/len(dev):.1%}', dict(conf))
for w in wrong[:60]:
    print(f'  gold={w[0]:5s} pred={w[1]:5s} ({w[2]:16s}) {w[3]}')
