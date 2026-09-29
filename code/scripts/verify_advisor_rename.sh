#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "=== 1) G1 残留 '导师' ==="
grep -n '导师' '/mnt/f/文献/AgentOps/实验记录/G1-约束抽检-第一批.md'
echo ""
echo "=== 2) MAPPING / README / SIGNOFF 中的 advisor 引用 ==="
grep -n 'advisor\|导师' '/mnt/f/文献/AgentOps/论文Q4/复现包/MAPPING.md' '/mnt/f/文献/AgentOps/论文Q4/复现包/README.md' '/mnt/f/文献/AgentOps/论文Q4/复现包/SIGNOFF.md' 2>/dev/null
echo ""
echo "=== 3) 复现包 recall 目录 ==="
ls '/mnt/f/文献/AgentOps/论文Q4/复现包/recall/' | head
echo ""
echo "=== 4) 校验 JSON 改名结果 ==="
$PY - <<'PYEOF'
import json
for p in ['/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json',
          '/mnt/f/文献/AgentOps/论文Q4/复现包/graph/constraint-graph.json']:
    d = json.load(open(p, encoding='utf-8'))
    m = d.get('meta', {})
    print(p.split('/')[-1], '->', {k: (v if not isinstance(v, dict) else list(v.keys())) for k, v in m.items() if k in ('independent_audit', 'advisor_review')})
    # 抽查 per-node 键
    n = d['nodes'][0]
    has_old = any('advisor' in str(k) for k in n.keys())
    print("   node0 含 advisor 键:", has_old, "| audit_note keys:", list(n.get('audit_note', {}).keys()) if isinstance(n.get('audit_note'), dict) else None)
    # 全文件残留
    txt = open(p, encoding='utf-8').read()
    print("   残留 'advisor' 次数:", txt.count('advisor'), "| '导师' 次数:", txt.count('导师'))
PYEOF
