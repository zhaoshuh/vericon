#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
$PY - <<'PYEOF'
import fitz, os
LAT = "/mnt/f/文献/AgentOps/论文/latex"
OUT = "/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2"
os.makedirs(OUT, exist_ok=True)
# 1) Fig2 单图高清
for name, dpi in [("fig2_types", 170), ("fig7_type_status", 170), ("fig6_status", 170)]:
    src = f"{LAT}/figs/{name}.pdf"
    if os.path.exists(src):
        doc = fitz.open(src)
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            p = f"{OUT}/FIG-{name}" + (f"-p{i+1}" if len(doc) > 1 else "") + ".png"
            pix.save(p)
            print("saved", p, pix.width, "x", pix.height)
# 2) 全文页
doc = fitz.open(f"{LAT}/main.pdf")
print("pages:", len(doc))
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=110)
    p = f"{OUT}/page{i+1:02d}.png"
    pix.save(p)
print("page renders done ->", OUT)
PYEOF
ls '/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2/' | head -25
