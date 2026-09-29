#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/figs/fig2_types.pdf")
pix = doc[0].get_pixmap(dpi=220)
pix.save("/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2/FIG-fig2-v2.png")
print("saved", pix.width, "x", pix.height)
PYEOF
