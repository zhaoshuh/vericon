#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "=== P1b-300汇总.json ==="
$PY - <<'PYEOF'
import json
d = json.load(open("/mnt/f/文献/AgentOps/实验记录/P1b-300汇总.json", encoding="utf-8"))
print(json.dumps(d, ensure_ascii=False, indent=1)[:1800])
PYEOF
echo ""
echo "=== P1b-金标准-结果-300.md 里的关键数字 ==="
grep -n '71\.9\|87\.2\|50\.8\|59\.5\|66%\|94%\|48%' /mnt/f/文献/AgentOps/实验记录/P1b-金标准-结果-300.md | head -12
echo ""
echo "=== ConstraintSampler 的环/拓扑处理 ==="
grep -rn 'cycle\|topo\|depend\|empty' /mnt/f/文献/AgentOps/代码/agentops/tune.py 2>/dev/null | head -10
ls /mnt/f/文献/AgentOps/代码/agentops/ 2>/dev/null | head
