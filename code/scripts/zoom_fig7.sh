#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main.pdf")
page = doc[7]  # p8
r = page.search_for("Dimension scaling and workload robustness")
print("caption rects:", r)
if r:
    clip = pymupdf.Rect(40, r[0].y0 - 165, page.rect.width / 2 + 5, r[0].y1 + 5)
    pix = page.get_pixmap(dpi=260, clip=clip)
    pix.save("/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2/FIG7-inpage-zoom.png")
    print("saved", pix.width, "x", pix.height)
PYEOF
