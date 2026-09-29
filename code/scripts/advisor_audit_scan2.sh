#!/usr/bin/env bash
pkill -f 'grep -rn' 2>/dev/null; sleep 0.5
PY=~/.venvs/agentops-py311/bin/python
$PY - <<'PYEOF'
import glob, os
pats = ('导师', 'advisor')
cands = []
cands += glob.glob('/mnt/f/文献/AgentOps/实验记录/*.md')
cands += ['/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json',
          '/mnt/f/文献/AgentOps/实验记录/约束图-v1.json',
          '/mnt/f/文献/AgentOps/实验记录/约束图-model2.json',
          '/mnt/f/文献/AgentOps/实验记录/约束图-sglang.json',
          '/mnt/f/文献/AgentOps/实验记录/G1-抽检样本-第一批.json',
          '/mnt/f/文献/AgentOps/实验记录/G1-抽检样本-第二批.json',
          '/mnt/f/文献/AgentOps/实验记录/已验证约束.json',
          '/mnt/f/文献/AgentOps/实验记录/已验证约束-跨引擎.json',
          '/mnt/f/文献/AgentOps/论文Q4/复现包/graph/constraint-graph.json',
          '/mnt/f/文献/AgentOps/论文Q4/复现包/graph/constraint-graph-ext.json',
          '/mnt/f/文献/AgentOps/论文Q4/复现包/graph/constraint-graph-sglang.json',
          '/mnt/f/文献/AgentOps/论文Q4/复现包/README.md']
cands += glob.glob('/mnt/f/文献/AgentOps/论文Q4/复现包/*.md')
cands += ['/mnt/f/文献/AgentOps/论文/latex/main.tex', '/mnt/f/文献/AgentOps/论文/latex/cover-letter.txt']
cands += ['/mnt/f/文献/AgentOps/论文/Paper1-draft-v2.md']
seen = set()
for f in cands:
    f = f.replace('\\', '/')
    if f in seen or not os.path.exists(f):
        continue
    seen.add(f)
    try:
        txt = open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for i, line in enumerate(txt.splitlines(), 1):
        if any(p in line for p in pats):
            print(f"{f}:{i}: {line.strip()[:150]}")
PYEOF
echo ""
echo "=== run2 进度 ==="
tail -2 '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/run2.log' 2>/dev/null | cut -c1-120
L=$(wc -l < '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/run2.log' 2>/dev/null)
echo "log lines: $L (≈330 行 = 完成)"
echo "--- calibration ---"
cat '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/calibration.csv' 2>/dev/null | tail -3
