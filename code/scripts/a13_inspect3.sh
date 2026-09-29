#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "===== 约束图-sglang.json ====="
$PY - <<'PYEOF'
import json
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/约束图-sglang.json', encoding='utf-8'))
print("keys:", list(d.keys())[:12])
print("meta:", json.dumps(d.get('meta', {}), ensure_ascii=False)[:400])
print("stats:", json.dumps(d.get('stats', {}), ensure_ascii=False)[:300])
for k, v in d.items():
    if isinstance(v, list):
        print(f"list '{k}': len={len(v)}")
PYEOF
echo ""
echo "===== third_party 中的 vLLM 版本 ====="
ls /mnt/f/文献/AgentOps/代码/third_party/ | head -20
echo ""
echo "===== 找 9670/585/242/262 的枚举产物 ====="
grep -rln '9670\|9,670' /mnt/f/文献/AgentOps/实验记录/*.json 2>/dev/null | head -5
ls /mnt/f/文献/AgentOps/实验记录/ | head -60
echo ""
echo "===== S6 报告 1-40 行 ====="
sed -n '1,40p' '/mnt/f/文献/AgentOps/实验记录/S6-真机锚点-报告.md'
echo ""
echo "===== S6 5rep wall 范围 ====="
$PY - <<'PYEOF'
import csv
rows = list(csv.DictReader(open('/mnt/f/文献/AgentOps/实验记录/llamacpp_anchor_5rep.csv', encoding='utf-8-sig')))
ws = [float(r['wall_s']) for r in rows]
print(f"wall_s min={min(ws):.1f} max={max(ws):.1f}")
top3 = sorted(rows, key=lambda r: -float(r['pp512_tps']))[:3]
for r in top3:
    print("top pp:", r['threads'], r['n_batch'], r['n_ubatch'], r['pp512_tps'], "tg:", r['tg64_tps'])
PYEOF
