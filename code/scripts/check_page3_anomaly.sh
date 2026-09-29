#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf, re
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main.pdf")
print("=== 各页 Fig. 题注顺序 ===")
for i, page in enumerate(doc):
    t = page.get_text()
    figs = re.findall(r"Fig\. (\d+)\.", t)
    if figs:
        print(f"p{i+1}: {figs}")
print()
print("=== p3 页首 300 字符 ===")
t3 = doc[2].get_text()
print(repr(t3[:300]))
PYEOF
