#!/usr/bin/env bash
cd "/mnt/f/文献/AgentOps/论文/latex"
python3 - <<'PY'
import re
log = open('main.log', encoding='utf-8', errors='replace').read()
# Overfull 块：形如 "Overfull \hbox (...) in paragraph at lines X--Y []" 后跟文本
blocks = re.findall(r"Overfull \\hbox \([^)]*\) (?:in paragraph )?at lines? (\d+)--?(\d+)?(.*?)(?=\n\n|\nOverfull|\nUnderfull|\Z)", log, re.S)
for i, (a, b, tail) in enumerate(blocks[:10], 1):
    txt = re.sub(r"\s+", " ", tail)[:200]
    print(f"--- [{i}] lines {a}-{b or a}")
    print(f"    {txt}")
PY
