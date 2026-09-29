#!/usr/bin/env bash
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
python - <<'PY'
import pymupdf
pdf = "/mnt/f/文献/AgentOps/论文/latex/main.pdf"
out = "/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染"
doc = pymupdf.open(pdf)
page = doc[0]
r = page.rect
print("page rect:", r)
# 左栏底部区域（占页面左半、下三分之一）
clip = pymupdf.Rect(r.x0, r.y0 + r.height * 0.62, r.x0 + r.width * 0.52, r.y1)
pix = page.get_pixmap(dpi=300, clip=clip)
pix.save(f"{out}/page01_左栏底部_300dpi.png")
print("saved cropped:", pix.width, pix.height)
PY
