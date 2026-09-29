#!/usr/bin/env bash
echo "== remaining stale marker =="
grep -n 'over-assertion\|not enforced by any version\|wrong from the start\|zero source-level hits' '/mnt/f/文献/AgentOps/论文/Paper1-draft-v2.md'
echo "== json nested check =="
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import json
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/S4验证/scoot-drift.json', encoding='utf-8'))
print("verdict_refined R2:", d['refinement_2026_09_27']['verdict_refined']['SCOOT#2'][:60])
print("verdict R2:", d['verdict']['SCOOT#2'][:60])
PYEOF
