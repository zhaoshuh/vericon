#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "===== 01-进度.md 中 ced6857 上下文 ====="
grep -n 'ced6857\|sglang' '/mnt/f/文献/AgentOps/01-进度.md' | head -10
echo ""
echo "===== Q4 文件中 ced6857 上下文 ====="
for f in '/mnt/f/文献/AgentOps/论文Q4/复现包/graph/constraint-graph-sglang.json' '/mnt/f/文献/AgentOps/论文Q4/复现包/README.md' '/mnt/f/文献/AgentOps/论文Q4/数据表-v1.md' '/mnt/f/文献/AgentOps/论文Q4/05-Evaluation.md' '/mnt/f/文献/AgentOps/论文Q4/Paper-Q4-draft-v1.md'; do
  echo "--- $f"
  grep -n 'ced6857' "$f" | head -3
done
echo ""
echo "===== Q4 sglang 图 meta ====="
$PY - <<'PYEOF'
import json, os
p = '/mnt/f/文献/AgentOps/论文Q4/复现包/graph/constraint-graph-sglang.json'
if os.path.exists(p):
    d = json.load(open(p, encoding='utf-8'))
    print("keys:", list(d.keys())[:8])
    print("meta:", json.dumps(d.get('meta', {}), ensure_ascii=False)[:250])
    print("stats:", json.dumps(d.get('stats', {}), ensure_ascii=False)[:150])
else:
    print("not exists")
PYEOF
echo ""
echo "===== 约束图-sglang.json 完整 meta ====="
$PY - <<'PYEOF'
import json
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/约束图-sglang.json', encoding='utf-8'))
print(json.dumps(d.get('meta', {}), ensure_ascii=False, indent=1))
PYEOF
echo ""
echo "===== main.tex 中 sglang 相关行 ====="
grep -n -i 'sglang' '/mnt/f/文献/AgentOps/论文/latex/main.tex' | head -8
