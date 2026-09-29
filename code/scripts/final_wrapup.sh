#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
p = "/mnt/f/文献/AgentOps/01-进度.md"
t = open(p, encoding="utf-8").read()
anchor = "| 2026-09-29 | S8c | **C2 扩展实验完成（第二主证据升级）**"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
row = ("| 2026-09-29 | S8c | **扩展实验终验 + 最终编译**：两轮复测（串行 `-r5` + **轮转 `-r3`**：每种子内 N/M/A/S 背靠背）→"
       " **可达吞吐无分离**（中位 48.5–63.3 t/s，区间完全重叠；环境波动 ±40% 主导绝对值）→ 约束改变的是搜索成本而非可达上限（与 S5 一致）；"
       "论文 §IV-F 补 \u201cFinal quality\u201d 句；文档（进度/整改计划/报告）收尾 |")
t = t[:j + 1] + row + "\n" + t[j + 1:]
open(p, "w", encoding="utf-8", newline="").write(t)
print("进度行已插入")
PYEOF
echo "=== 最终编译 ==="
bash /mnt/f/文献/AgentOps/代码/scripts/compile_with_texlive.sh 2>&1 | grep -E '✅|Overfull|pages' | head -4
LOG=/mnt/f/文献/AgentOps/论文/latex/main.log
echo -n "Overfull: "; grep -c 'Overfull' "$LOG" || true
echo -n "undefined: "; grep -c 'undefined' "$LOG" || true
grep -o 'Output written on main.pdf ([0-9]* pages' "$LOG" | head -1
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import re
lines = open('/mnt/f/文献/AgentOps/论文/latex/main.tex', encoding='utf-8').read().splitlines()
for i, l in enumerate(lines):
    if l.strip() == r'\begin{abstract}':
        body = lines[i+1]
        body = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?', ' ', body)
        body = re.sub(r'[{}\\~$]', ' ', body)
        print('abstract words:', len([w for w in body.split() if any(c.isalnum() for c in w)]), '(<=250)')
        break
PYEOF
