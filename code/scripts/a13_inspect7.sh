#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "===== ext 图 node 样例与 tier ====="
$PY - <<'PYEOF'
import json
from collections import Counter
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json', encoding='utf-8'))
nodes = d['nodes']
print("sample extraction:", json.dumps(nodes[0].get('extraction'), ensure_ascii=False)[:300])
print("sample validation:", json.dumps(nodes[0].get('validation'), ensure_ascii=False)[:200])
# tier 分类
def tier(x):
    ex = x.get('extraction')
    if isinstance(ex, dict):
        return ex.get('tier') or ex.get('model') or tuple(ex.items())
    return ex
c = Counter(str(tier(x))[:60] for x in nodes)
for k, v in c.most_common(8):
    print(f"  tier {k}: {v}")
print("evidence non-empty:", sum(1 for x in nodes if str(x.get('evidence', '')).strip()))
print("by_type:", dict(Counter(x.get('type') for x in nodes)))
sc = Counter(x.get('scope') for x in nodes)
print("by_scope:", dict(sc))
PYEOF
echo ""
echo "===== 含 sglang 且含 ced6857 的文件 ====="
for f in $(grep -rln 'ced6857' /mnt/f/文献/AgentOps --include='*.json' --include='*.md' 2>/dev/null | grep -v third_party); do
  if grep -qi 'sglang' "$f" 2>/dev/null; then echo "$f"; fi
done
echo ""
echo "===== reextract_sources.py sglang 条目 ====="
sed -n '1,40p' /mnt/f/文献/AgentOps/代码/scripts/reextract_sources.py
echo "--- 清单/哈希文件 ---"
find /mnt/f/文献/AgentOps/代码/third_party -maxdepth 2 -name '*manifest*' -o -maxdepth 2 -name '*sha*' -o -maxdepth 2 -name '*.tar.gz' 2>/dev/null | head -8
