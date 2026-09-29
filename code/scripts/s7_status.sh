#!/usr/bin/env bash
echo "== S7 已完成 study 及非法率 =="
for d in /mnt/f/文献/AgentOps/实验记录/optuna/s7-*/; do
  name=$(basename "$d")
  csv="$d/trials.csv"
  [ -f "$csv" ] || continue
  python3 - "$csv" "$name" <<'PY'
import csv, sys
p, name = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(p, encoding='utf-8-sig')))
n = len(rows)
nf = sum(1 for r in rows if (r.get('user_attrs_status') or 'ok') != 'ok')
cost = sum(float(r.get('user_attrs_experiment_units') or 0) for r in rows)
print(f'{name}: n={n} failed={nf} cost={cost:.1f}')
PY
done
