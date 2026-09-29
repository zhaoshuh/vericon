#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main.pdf")
for i, page in enumerate(doc):
    if page.search_for("Final quality"):
        pix = page.get_pixmap(dpi=115)
        pix.save(f"/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2/page{i+1:02d}-final.png")
        print("rendered page", i + 1)
PYEOF
