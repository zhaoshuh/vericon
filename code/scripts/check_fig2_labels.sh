#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/figs/fig2_types.pdf")
page = doc[0]
words = page.get_text("words")
cats = [w for w in words if w[4] in ("implication", "mutual_exclusion", "range", "arithmetic", "enum", "inequality", "type")]
print("类别标签位置（旋转文字，取 bbox 中心 x）:")
cats = sorted(cats, key=lambda w: w[0])
bar_centers = [68.67, 101.51, 134.35, 167.20, 200.04, 232.89, 265.74]
for i, w in enumerate(cats):
    cx = (w[0] + w[2]) / 2
    print(f"  {w[4]:18s} bbox_x=({w[0]:.1f},{w[2]:.1f}) center_x={cx:.1f} | 柱{i+1} x={bar_centers[i]:.1f} | dx={cx-bar_centers[i]:+.1f}")
PYEOF
