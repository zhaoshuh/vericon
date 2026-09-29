#!/usr/bin/env bash
python3 - <<'PY'
import csv, glob, os
base = '/mnt/f/文献/AgentOps/实验记录/optuna/'
for tag in ('s7-arxiv-N', 's7-code-N', 's5-N'):
    pats = sorted(glob.glob(base + tag + '-seed*/trials.csv'))
    if not pats:
        pats = sorted(glob.glob(base + tag.replace('s5-N', 's5-N-seed') + '*/trials.csv'))
    failed_mtib = []
    ok_mtib = []
    for p in pats[:5]:
        for r in csv.DictReader(open(p, encoding='utf-8-sig')):
            mtib = r.get('params_max_num_batched_tokens')
            if not mtib:
                continue
            mtib = int(float(mtib))
            if (r.get('user_attrs_status') or 'ok') != 'ok':
                failed_mtib.append(mtib)
            else:
                ok_mtib.append(mtib)
    failed_mtib.sort()
    ok_mtib.sort()
    print(f'{tag}: failed n={len(failed_mtib)} mtib范围={failed_mtib[:3]}...{failed_mtib[-3:] if failed_mtib else []}')
    print(f'        ok     n={len(ok_mtib)} min_ok_mtib={ok_mtib[0] if ok_mtib else None}')
PY
