#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "===== 各版本 flags：注册数 vs 去重数 ====="
$PY - <<'PYEOF'
import json, glob, os
for f in sorted(glob.glob('/mnt/f/文献/AgentOps/实验记录/P2-版本研究/v*-params.json')):
    d = json.load(open(f, encoding='utf-8'))
    f_list = d.get('cli_flags', [])
    names = set()
    for x in f_list:
        names.add(x.get('flag') if isinstance(x, dict) else str(x))
    v = os.path.basename(f).replace('-params.json', '')
    print(f"{v}: counts.cli_flags={d.get('counts', {}).get('cli_flags')}  len={len(f_list)}  distinct={len(names)}")
PYEOF
echo ""
echo "===== ced6857 出现文件 ====="
grep -rln 'ced6857' /mnt/f/文献/AgentOps --include='*.json' --include='*.md' --include='*.tex' --include='*.txt' 2>/dev/null | grep -v third_party | head -20
echo ""
echo "===== ext 图：tier 字段与统计重算 ====="
$PY - <<'PYEOF'
import json
from collections import Counter
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json', encoding='utf-8'))
nodes = d['nodes']
print("nodes:", len(nodes))
ext = Counter(x.get('extraction', '?') for x in nodes)
print("extraction dist:", dict(ext))
print("n with non-empty evidence:", sum(1 for x in nodes if str(x.get('evidence', '')).strip()))
print("by_type:", dict(Counter(x.get('type') for x in nodes)))
print("by_scope:", dict(Counter(x.get('scope') for x in nodes)))
print("meta:", json.dumps(d.get('meta', {}), ensure_ascii=False)[:300])
PYEOF
