#!/usr/bin/env bash
cd /mnt/f/文献/AgentOps
# 合成测试 CSV：tier1 全 Y，tier2 交替，tier3 全 N
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import json, csv
pack = json.load(open('实验记录/C1-人类盲标/sites-pack.json', encoding='utf-8'))['items']
with open('实验记录/C1-人类盲标/c1_results.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f); w.writerow(['id', 'verdict', 'note', 'file', 'line', 'tier'])
    for i, it in enumerate(pack):
        v = 'Y' if it['tier'] == 1 else ('N' if it['tier'] == 3 else ('Y' if i % 2 else 'N'))
        w.writerow([it['id'], v, '', it['file'], it['line'], it['tier']])
print("synthetic csv written")
PYEOF
~/.venvs/agentops-py311/bin/python 代码/scripts/c1_import_results.py
rm -f 实验记录/C1-人类盲标/c1_results.csv 实验记录/C1-人类盲标/C1-导入结果.json
echo "== cleaned =="
ls 实验记录/C1-人类盲标/
