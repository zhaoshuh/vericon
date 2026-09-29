#!/usr/bin/env bash
echo "=== 编译 ==="
bash /mnt/f/文献/AgentOps/代码/scripts/compile_with_texlive.sh 2>&1 | grep -E '✅|Overfull|Error' | head -5
LOG=/mnt/f/文献/AgentOps/论文/latex/main.log
echo -n "Overfull: "; grep -c 'Overfull' "$LOG" || true
echo -n "undefined: "; grep -c 'undefined' "$LOG" || true
grep -o 'Output written on main.pdf ([0-9]* pages' "$LOG" | head -1
echo ""
echo "=== 摘要词数 ==="
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import re
lines = open('/mnt/f/文献/AgentOps/论文/latex/main.tex', encoding='utf-8').read().splitlines()
def _cnt(latex):
    s = latex
    s = re.sub(r'\\textbf\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\emph\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\code\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\%', '%', s)
    s = re.sub(r'\\[a-zA-Z]+(\[[^\]]*\])?(\{[^{}]*\})?', ' ', s)
    s = re.sub(r'[{}$\\]', ' ', s)
    return len([w for w in s.split() if any(c.isalnum() for c in w)])
for i, l in enumerate(lines):
    if l.strip() == r'\begin{abstract}':
        print('abstract words (correct):', _cnt(lines[i+1]), '(<=250)')
        break
PYEOF
echo ""
echo "=== 残留 Theorem / 检查关键新句 ==="
grep -c 'Theorem' /mnt/f/文献/AgentOps/论文/latex/main.tex || true
grep -n 'Witness-level confirmation\|Zero-violation sampling\|constraint-level design weighting\|via the construction path' /mnt/f/文献/AgentOps/论文/latex/main.tex | head -8
