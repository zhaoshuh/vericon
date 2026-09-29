#!/usr/bin/env bash
echo "=== 编译 ==="
bash /mnt/f/文献/AgentOps/代码/scripts/compile_with_texlive.sh 2>&1 | tail -18
echo ""
echo "=== 关键检查 ==="
LOG=/mnt/f/文献/AgentOps/论文/latex/main.log
echo -n "Overfull: "; grep -c 'Overfull' "$LOG" || true
echo -n "undefined refs/cites: "; grep -c 'undefined' "$LOG" || true
echo -n "页数: "; grep -o 'Output written on main.pdf ([0-9]* pages' "$LOG" | head -1
echo ""
echo "=== 摘要词数 ==="
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import re
lines = open('/mnt/f/文献/AgentOps/论文/latex/main.tex', encoding='utf-8').read().splitlines()
for i, l in enumerate(lines):
    if l.strip() == r'\begin{abstract}':
        body = lines[i+1]
        body = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?', ' ', body)
        body = re.sub(r'[{}\\~$]', ' ', body)
        words = [w for w in body.split() if any(c.isalnum() for c in w)]
        print('abstract words:', len(words), '(上限 250)')
        break
PYEOF
echo ""
echo "=== 12-签字单 等中的悬空引用检查 ==="
grep -n '复核意见' '/mnt/f/文献/AgentOps/论文Q4/12-签字单.md' '/mnt/f/文献/AgentOps/论文Q4/复现包/SIGNOFF.md' 2>/dev/null | head -5
echo "(无输出=无引用)"
