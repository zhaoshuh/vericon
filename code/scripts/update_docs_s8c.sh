#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
AP = "/mnt/f/文献/AgentOps"

# ---- 进度文档 ----
p = f"{AP}/01-进度.md"
t = open(p, encoding="utf-8").read()
anchor = "| 2026-09-29 | 论文 | **视觉复审 + Fig.2 重构**"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
rows = [
 ("| 2026-09-29 | 论文 | **叙事改造（衰减成为第一发现）**：新增 **Fig.1 漂移时间线**（三规则×六版本，矢量级复核通过）；摘要重写为衰减开场"
  "（顺手修复摘要中残留 Markdown `**` 渲染 bug）；贡献#1 → “A measured decay of hand-written constraint knowledge”；引言观察段/结论/cover letter 问题段全部衰减优先；重编译 11 页 0 Overfull |"),
 ("| 2026-09-29 | S8c | **C2 扩展实验完成（第二主证据升级）**：Qwen2.5-**1.5B**、六维 **216 组合**、**四臂（N/M/A/S，含 SCOOT 式在线学习）** × 5 种子 × 20 trials = **400 次真实推理**（trial 级交错 + 校准监测）；"
  "**非法率：A 0% / S 5%（每种子恰付 1 次发现费后学会）/ M 12% / N 17%**（34 次失败 100% 恰为 ctv=q8_0∧fa=off）；成本 **A 20.0 < S 23.0（−13.0%，配对 CI [3.0,3.0]）< M 27.2（−26.5%）< N 30.2（−33.8%）**；"
  "M/S **0 次**探索合法 ubatch>batch 区（A 11/100、N 14/83）；另实测修正真机约束为**仅 V-cache**（ctk=q8_0 无需 FA）；论文 §IV-F/摘要/贡献#4/cover letter 已同步；产物 `trials-ext.csv`、`S8-ext-汇总.json` |"),
]
t = t[:j + 1] + "\n".join(rows) + "\n" + t[j + 1:]
open(p, "w", encoding="utf-8", newline="").write(t)
print("进度 +2 行")

# ---- 整改计划 C2 行 ----
pp = f"{AP}/论文/审稿模拟/审稿汇总与整改计划.md"
t = open(pp, encoding="utf-8").read()
old = "；论文 \u00a7RQ5/摘要/贡献#4 + cover letter 已回填 |"
n = t.count(old)
print("计划 C2 行匹配:", n)
if n == 1:
    t = t.replace(old, "；论文 §RQ5/摘要/贡献#4 + cover letter 已回填。**扩展版（2026-09-29 晚，第二主证据）**：1.5B/六维/四臂（含 SCOOT 式在线学习 S）/400 次推理 → 非法 0%（A）/5%（S）/12%（M）/17%（N），A 成本低 13–34%；论文已按扩展版更新；终验 -r5 复测运行中 |")
    open(pp, "w", encoding="utf-8", newline="").write(t)
    print("计划已更新")
PYEOF
