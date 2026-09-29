#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main.pdf")
page = doc[4]  # p5
# 找 Fig.2 标题的 y 位置（"Extracted constraint types" 文本是矢量图内文字）
r = page.search_for("Extracted constraint types")
print("fig title rects:", r)
cap = page.search_for("Constraint type distribution")
print("caption rects:", cap)
if r:
    y0, y1 = r[0].y0 - 30, (cap[0].y1 if cap else r[0].y1) + 10
    clip = pymupdf.Rect(60, y0, page.rect.width - 60, y1)
    pix = page.get_pixmap(dpi=300, clip=clip)
    pix.save("/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2/FIG2-inpage-zoom.png")
    print("saved zoom", pix.width, "x", pix.height)
PYEOF
