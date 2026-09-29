#!/usr/bin/env bash
echo "--- md 中该句 ---"
grep -n '23 parallel' '/mnt/f/文献/AgentOps/论文/Paper1-draft-v2.md' | head -3
echo "--- tex fig:types 引用 ---"
grep -n 'fig:types' '/mnt/f/文献/AgentOps/论文/latex/main.tex'
echo "--- 图文件与数据 ---"
ls '/mnt/f/文献/AgentOps/实验记录/' | grep -c '约束图.json'
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import json
from collections import Counter
old = json.load(open('/mnt/f/文献/AgentOps/实验记录/约束图.json', encoding='utf-8'))
new = json.load(open('/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json', encoding='utf-8'))
c_old = Counter(n['type'] for n in old['nodes'])
c_new = Counter(n['type'] for n in new['nodes'])
print('core 282:', dict(sorted(c_old.items(), key=lambda kv: -kv[1])), '| sum =', sum(c_old.values()))
print('ext  716:', dict(sorted(c_new.items(), key=lambda kv: -kv[1])), '| sum =', sum(c_new.values()))
d = {k: c_new[k] - c_old.get(k, 0) for k in c_new}
print('extension = 716-core:', dict(sorted(d.items(), key=lambda kv: -kv[1])), '| sum =', sum(d.values()))
PYEOF
