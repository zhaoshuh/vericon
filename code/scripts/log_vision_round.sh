#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
p = "/mnt/f/文献/AgentOps/01-进度.md"
t = open(p, encoding="utf-8").read()
anchor = "| 2026-09-29 | C1 | **第三遍独立盲标完成"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
row = ("| 2026-09-29 | 论文 | **视觉复审 + Fig.2 重构**：11 页逐页目检 + 矢量级校验（Fig.2 柱高/数值标注/类别对齐逐项核验、Fig.7 百分比与正文一致、"
       "无图-文重叠/裁切）；**Fig.2 由「282 total」重构为全量 716 堆叠图（282 core + 434 extension）**，题注与正文引用同步；"
       "修正 RQ2 段反向引用 `(Figures 4 and 3)` → `(Figure 3)`；重编译 11 页 0 Overfull、0 undefined |")
t = t[:j + 1] + row + "\n" + t[j + 1:]
open(p, "w", encoding="utf-8", newline="").write(t)
print("进度行已插入")
PYEOF
