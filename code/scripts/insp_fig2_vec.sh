#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/figs/fig2_types.pdf")
page = doc[0]
# 柱子 = 填充矩形
bars = []
for d in page.get_drawings():
    for it in d["items"]:
        if it[0] == "re":
            r = it[1]
            if r.width > 5 and r.height > 5:
                bars.append(r)
bars = sorted(bars, key=lambda r: (round(r.y1), r.x0))
print(f"rects: {len(bars)}")
for r in bars:
    print(f"  x0={r.x0:7.2f} y0={r.y0:7.2f} w={r.width:6.2f} h={r.height:7.2f} y1={r.y1:7.2f}")
# 数字标注
txt = page.get_text("words")
nums = [(w[4], w[0], w[1]) for w in txt if w[4].replace('.', '').isdigit()]
print("numbers in figure:")
for n in nums:
    print("  ", n)
# y 轴刻度（0/50/100 对应像素）
axis = [(w[4], w[1]) for w in txt if w[4] in ("0", "50", "100")]
print("axis labels:", axis)
PYEOF
echo ""
echo "=== 找生成脚本 ==="
ls /mnt/f/文献/AgentOps/代码/scripts/ | grep -i 'fig' | head -20
