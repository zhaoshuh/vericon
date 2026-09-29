#!/usr/bin/env bash
echo "=== 0) Q4 复现包中是否有 advisor 命名的文件 ==="
find '/mnt/f/文献/AgentOps/论文Q4/复现包' -iname '*advisor*' -o -iname '*导师*' 2>/dev/null
ls '/mnt/f/文献/AgentOps/论文Q4/复现包/' 2>/dev/null
echo ""
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
import os
import shutil
import re

AP = "/mnt/f/文献/AgentOps"

def edit_text(path, pairs, require_zero_after=None):
    raw = open(path, encoding="utf-8").read()
    for old, new in pairs:
        raw = raw.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(raw)
    if require_zero_after:
        left = raw.count(require_zero_after)
        print(f"  {os.path.basename(path)}: 剩余 '{require_zero_after}' = {left}")

def stream_json_replace(path, pairs):
    """流式文本替换（低内存），带 .bak"""
    bak = path + ".pre-advisor-rename.bak"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    src = open(path, encoding="utf-8")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as out:
        for line in src:
            for old, new in pairs:
                if old in line:
                    line = line.replace(old, new)
            out.write(line)
    src.close()
    os.replace(tmp, path)
    print(f"  {os.path.basename(path)}: 流式替换完成")

# ---------- 1) 三个约束图 JSON（文本级） ----------
json_pairs = [
    ('"advisor_review"', '"independent_audit"'),
    ('"advisor_2026-09-27"', '"audit_2026-09-27"'),
    ('导师复核注：', '独立复核注：'),
    ('导师补证', '独立复核补证'),
    ('导师复核', '独立复核'),
    ('"scope": "两批独立抽样共 40 条（seed 42 / seed 20260927），0 错误；G1 复核通过"',
     '"scope": "两批独立抽样共 40 条（seed 42 / seed 20260927），0 错误；G1 复核通过", "role": "独立复核实例（AI；非外部人员）"'),
]
print("[1] 约束图 JSON：")
for p in [f"{AP}/实验记录/约束图-v1-ext.json",
          f"{AP}/论文Q4/复现包/graph/constraint-graph.json",
          f"{AP}/论文Q4/复现包/graph/constraint-graph-ext.json"]:
    if os.path.exists(p):
        stream_json_replace(p, json_pairs)
    else:
        print("  (missing)", p)

# ---------- 2) G1 记录 ----------
print("[2] G1 记录：")
edit_text(f"{AP}/实验记录/G1-约束抽检-第一批.md", [
    ("**已由导师角色完成独立复核（2026-09-27，见下节）**", "**已由独立复核角色（AI 实例）完成独立复核（2026-09-27，见下节）**"),
    ("## 导师复核（2026-09-27）：第二批独立抽样", "## 独立复核（2026-09-27）：第二批独立抽样"),
    ("导师角色**独立重新抽样**", "独立复核角色（AI 实例）**独立重新抽样**"),
    ("**导师补证**：", "**独立复核补证**："),
    ("**导师复核结论**：", "**独立复核结论**："),
    ("复核人：导师角色（AI 扮演，供用户最终确认）", "复核人：独立复核角色（AI 实例；非外部人员）"),
    ("（导师复核第二批）", "（独立复核第二批）"),
], require_zero_after="导师")

# ---------- 3) 导师复核意见书 → 独立复核意见书（改名+内容） ----------
print("[3] 复核意见书：")
old_f = f"{AP}/实验记录/导师复核意见-2026-09-27.md"
new_f = f"{AP}/实验记录/独立复核意见-2026-09-27.md"
if os.path.exists(old_f):
    t = open(old_f, encoding="utf-8").read()
    t = t.replace("# 导师复核意见书（2026-09-27）", "# 独立复核意见书（2026-09-27）")
    t = t.replace("复核人：导师角色（应用户要求由 AI 扮演，最终仍需真实导师确认）",
                  "复核人：独立复核角色（AI 实例；非外部人员；本项目无学术导师参与）")
    t = t.replace("（含导师复核节）", "（含独立复核节）")
    t = t.replace("目前是\"执行者 → AI 导师\"两级，仍缺**真实人**（本人/导师）确认",
                  "目前是\"执行者 → 独立 AI 复核\"两级，仍缺**真实人**确认")
    t = t.replace("用户（或导师）在 G1 记录上补签", "用户（或同事）在 G1 记录上补签")
    t = t.replace("复核人：导师角色（AI 扮演）｜ 日期：2026-09-27 ｜ 待真实导师/用户确认",
                  "复核人：独立复核角色（AI 实例）｜ 日期：2026-09-27 ｜ 待用户/人类签核确认")
    t = t.replace("导师", "独立复核")
    open(new_f, "w", encoding="utf-8", newline="").write(t)
    os.remove(old_f)
    print(f"  已改名 → 独立复核意见-2026-09-27.md；剩余'导师' =", t.count("导师"))

# ---------- 4) S3 / S6 / 论文 md / MAPPING ----------
print("[4] 其他引用：")
edit_text(f"{AP}/实验记录/S3-抽取报告.md", [
    ("响应导师复核 A1", "响应独立复核 A1"),
    ("**需用户/导师复核签字**", "**需用户/人类（非 AI）复核签字**"),
], require_zero_after="导师")
edit_text(f"{AP}/实验记录/S6-真机锚点-报告.md", [
    ("（advisor A3 关闭）", "（独立复核 A3 关闭）"),
], require_zero_after="advisor")
edit_text(f"{AP}/论文/Paper1-draft-v2.md", [
    ("`导师复核意见-2026-09-27.md`", "`独立复核意见-2026-09-27.md`"),
], require_zero_after="导师")
mp = f"{AP}/论文Q4/复现包/MAPPING.md"
if os.path.exists(mp):
    edit_text(mp, [("`实验记录/导师复核意见-2026-09-27.md`", "`实验记录/独立复核意见-2026-09-27.md`")])

print("RENAME-DONE")
PYEOF
