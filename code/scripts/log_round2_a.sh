#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
p = "/mnt/f/文献/AgentOps/01-进度.md"
t = open(p, encoding="utf-8").read()
anchor = "| 2026-09-29 | 论文 | **模型信息披露**"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
row = ("| 2026-09-29 | 审稿模拟 | **第二轮三审完成 + A 批整改（13 项）**：三名全新上下文审稿人（配置分析/服务系统/实证方法）均判 **Major**；"
       "完成：收益归因重述（M≡A 显式化、指向 RQ1–RQ4 与真机）、独立框口径修正（撤回 corroborates；同口径 CI 不相交=范围差异）、"
       "**约束级设计加权 53.0%/63.2%**（独立复算与审稿人一致）、Theorem 1/2 → **Proposition 1/2**（见证级 + 非空域假设 + 实测 7 环）、"
       "摘要补 construction-path、S 臂 9.5% 统一、0.5B/1.5B 澄清、审计来源披露、单标注者披露；脚本化 17 处替换全命中；重编译 11 页 0 Overfull/0 undefined、摘要 223 词；"
       "映射表 `论文/审稿模拟/第二轮-整改映射-2026-09-29.md`；**B 批（人类盲标）待用户找人；C 批（GPU/V1 锚点）建议返修期** |")
t = t[:j + 1] + row + "\n" + t[j + 1:]
open(p, "w", encoding="utf-8", newline="").write(t)
print("进度行已插入")
PYEOF
