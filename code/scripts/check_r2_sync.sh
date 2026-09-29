#!/usr/bin/env bash
echo "== stale markers in md =="
grep -c 'over-assertion\|not enforced by any version\|wrong from the start\|zero source-level hits' '/mnt/f/文献/AgentOps/论文/Paper1-draft-v2.md' || echo "0 (grep exit $?)"
echo "== corrected rows =="
grep -n 'removed later (decay)' '/mnt/f/文献/AgentOps/论文/Paper1-draft-v2.md' | head -3
echo "== json check =="
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import json
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/S4验证/scoot-drift.json', encoding='utf-8'))
print("correction:", d['correction_2026_09_29']['narrative'][:70])
print("verdict_refined R2:", d['verdict_refined']['SCOOT#2'][:50])
print("verdict R2:", d['verdict']['SCOOT#2'][:50])
PYEOF
