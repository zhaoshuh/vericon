#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
p = "/mnt/f/文献/AgentOps/01-进度.md"
t = open(p, encoding="utf-8").read()
anchor = "| 2026-09-29 | S8c | **扩展实验终验 + 最终编译**"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
row = ("| 2026-09-29 | 论文 | **模型信息披露**：§III-D 首次出现处标注主抽取模型 **deepseek-v4.1-flash**；§IV-C 跨模型复现改为"
       " \u201cGLM-5.3-Flash vs. deepseek-v4.1-flash (primary)\u201d（gpt-6-luna 因区域限制不可用的记录见 `实验记录/S3-抽取报告.md`；全流程零 OpenAI 依赖） |")
t = t[:j + 1] + row + "\n" + t[j + 1:]
open(p, "w", encoding="utf-8", newline="").write(t)
print("进度行已插入")
PYEOF
echo "=== 编译 ==="
bash /mnt/f/文献/AgentOps/代码/scripts/compile_with_texlive.sh 2>&1 | grep -E '✅|pages' | head -3
LOG=/mnt/f/文献/AgentOps/论文/latex/main.log
echo -n "Overfull: "; grep -c 'Overfull' "$LOG" || true
echo -n "undefined: "; grep -c 'undefined' "$LOG" || true
grep -o 'Output written on main.pdf ([0-9]* pages' "$LOG" | head -1
