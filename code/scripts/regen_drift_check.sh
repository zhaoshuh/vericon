#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python /mnt/f/文献/AgentOps/代码/scripts/regen_drift_fig.py && ~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open('/mnt/f/文献/AgentOps/论文/latex/figs/fig_drift_rules.pdf')
pix = doc[0].get_pixmap(dpi=220)
pix.save('/mnt/f/文献/AgentOps/论文/审稿模拟/页面渲染2/FIG-drift2.png')
print('rendered', pix.width, 'x', pix.height)
PYEOF
