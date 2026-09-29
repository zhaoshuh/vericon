#!/usr/bin/env bash
# 安装 PyMuPDF（若缺）并把 PDF 逐页渲染为 PNG（供视觉审查）
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"

python -c "import fitz" 2>/dev/null || pip install -q pymupdf -i https://pypi.tuna.tsinghua.edu.cn/simple
python - <<'PY'
import fitz, os
pdf = "/mnt/f/文献/AgentOps/论文/latex/main.pdf"
out = "/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染"
os.makedirs(out, exist_ok=True)
doc = fitz.open(pdf)
print("pages:", len(doc))
for i, page in enumerate(doc, 1):
    pix = page.get_pixmap(dpi=160)
    p = f"{out}/page{i:02d}.png"
    pix.save(p)
    print("saved", p, f"{pix.width}x{pix.height}")
PY
