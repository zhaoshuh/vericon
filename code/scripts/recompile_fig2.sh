#!/usr/bin/env bash
echo "=== 重编译 ==="
bash /mnt/f/文献/AgentOps/代码/scripts/compile_with_texlive.sh 2>&1 | grep -E '✅|Overfull|pages' | head -5
LOG=/mnt/f/文献/AgentOps/论文/latex/main.log
echo -n "Overfull: "; grep -c 'Overfull' "$LOG" || true
echo -n "undefined: "; grep -c 'undefined' "$LOG" || true
grep -o 'Output written on main.pdf ([0-9]* pages' "$LOG" | head -1
echo ""
echo "=== 重渲染 p5（新 Fig2 in place）==="
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main.pdf")
for i in (4,):
    pix = doc[i].get_pixmap(dpi=110)
    pix.save(f"/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2/page{i+1:02d}-v2.png")
    print("saved page", i + 1)
PYEOF
