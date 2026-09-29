#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main.pdf")
for i, page in enumerate(doc):
    if page.search_for("lifecycle of SCOOT"):
        print("drift fig caption on page", i + 1)
        pix = page.get_pixmap(dpi=110)
        pix.save(f"/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2/page{i+1:02d}-v3.png")
    if page.search_for("Hand-written configuration knowledge does not last"):
        print("new abstract on page", i + 1)
        pix = page.get_pixmap(dpi=110)
        pix.save(f"/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2/page{i+1:02d}-abstract.png")
    if page.search_for("**"):
        print("WARNING: literal ** found on page", i + 1)
PYEOF
