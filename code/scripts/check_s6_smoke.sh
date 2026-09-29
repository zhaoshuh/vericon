#!/usr/bin/env bash
python3 - <<'PY'
import csv
p = '/tmp/agentops-s6/optuna/s6-S-seed1/trials.csv'
rows = list(csv.DictReader(open(p, encoding='utf-8-sig')))
print('trials:', len(rows))
for r in rows:
    print('n=%s status=%s mtib=%s floor=%s units=%s value=%s' % (
        r['number'], r.get('user_attrs_status'),
        r.get('params_max_num_batched_tokens'),
        r.get('user_attrs_learned_floor'),
        r.get('user_attrs_experiment_units'), r.get('value')))
PY
