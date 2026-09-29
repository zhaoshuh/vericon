#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import json
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json', encoding='utf-8'))
m = d.get('meta', {})
print(json.dumps({k: v for k, v in m.items() if k != 'parts_dir'}, ensure_ascii=False, indent=1)[:900])
PYEOF
echo "=== Q4 复现包里是否有同样字段 ==="
grep -l 'advisor_review' /mnt/f/文献/AgentOps/论文Q4/复现包/graph/*.json /mnt/f/文献/AgentOps/论文/latex/* 2>/dev/null
echo "=== 主图（v1 282）meta 是否有 ==="
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import json
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/约束图-v1.json', encoding='utf-8'))
print(list(d.get('meta', {}).keys()))
PYEOF
