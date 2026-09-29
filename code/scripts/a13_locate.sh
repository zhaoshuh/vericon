#!/usr/bin/env bash
echo "== 1) SGLang 图 meta.commit =="
find /mnt/f/文献/AgentOps -name '约束图*ext*.json' -o -name '约束图-SGLang*.json' 2>/dev/null | head -5
for f in $(find /mnt/f/文献/AgentOps -name '*SGLang*.json' -o -name '*sglang*.json' 2>/dev/null | grep -v 审稿 | head -4); do
  echo "--- $f"
  ~/.venvs/agentops-py311/bin/python - "$f" <<'PYEOF'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding='utf-8'))
    m = d.get('meta', {})
    print("meta:", {k: str(v)[:60] for k, v in m.items() if k in ('commit','version','engine','file','repo')})
    print("stats:", d.get('stats', {}))
except Exception as e:
    print("ERR", e)
PYEOF
done
echo ""
echo "== 2) 约束图-v1-ext stats.total =="
find /mnt/f/文献/AgentOps -name '约束图-v1-ext.json' 2>/dev/null | while read f; do
  echo "--- $f"
  ~/.venvs/agentops-py311/bin/python - "$f" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
print("stats:", d.get('stats', {}))
cons = d.get('constraints', d.get('items', []))
print("len(constraints):", len(cons))
PYEOF
done
echo ""
echo "== 3) 版本对比.md 259/262 =="
grep -n '259\|262' '/mnt/f/文献/AgentOps/实验记录/P2-版本研究/版本对比.md' | head -10
echo ""
echo "== 4) S6 报告 165.4 / 159.77 =="
grep -n '165\.4\|159\.77' '/mnt/f/文献/AgentOps/实验记录/S6-真机锚点-报告.md' 2>/dev/null | head -10
