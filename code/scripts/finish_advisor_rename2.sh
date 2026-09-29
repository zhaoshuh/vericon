#!/usr/bin/env bash
echo "=== A) 全项目（限 md/tex/txt，排除 third_party）残留 '导师|advisor' ==="
grep -rn '导师\|advisor' \
  /mnt/f/文献/AgentOps/论文 /mnt/f/文献/AgentOps/论文Q4 /mnt/f/文献/AgentOps/实验记录 \
  /mnt/f/文献/AgentOps/*.md \
  --include='*.md' --include='*.tex' --include='*.txt' 2>/dev/null \
  | grep -v third_party | head -40
echo "(以上为全部命中)"
echo ""
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
AP = "/mnt/f/文献/AgentOps"

PAIRS_G1 = [
    ("**已由导师角色完成独立复核（2026-09-27，见下节）**", "**已由独立复核角色（AI 实例）完成独立复核（2026-09-27，见下节）**"),
    ("## 导师复核（2026-09-27）：第二批独立抽样", "## 独立复核（2026-09-27）：第二批独立抽样"),
    ("导师角色**独立重新抽样**", "独立复核角色（AI 实例）**独立重新抽样**"),
    ("**导师补证**：", "**独立复核补证**："),
    ("**导师复核结论**：", "**独立复核结论**："),
    ("**签字**：导师复核通过", "**签字**：独立复核通过"),
    ("复核人：导师角色（AI 扮演，供用户最终确认）", "复核人：独立复核角色（AI 实例；非外部人员）"),
    ("（导师复核第二批）", "（独立复核第二批）"),
]
PAIRS_S3 = [
    ("响应导师复核 A1", "响应独立复核 A1"),
    ("**需用户/导师复核签字**", "**需用户/人类（非 AI）复核签字**"),
]

def apply(path, pairs):
    t = open(path, encoding="utf-8").read()
    before = t
    for o, n in pairs:
        t = t.replace(o, n)
    t = t.replace("导师", "独立复核")  # 兜底
    if t != before:
        open(path, "w", encoding="utf-8", newline="").write(t)
    print(f"  {path.split('AgentOps/')[-1]}: 修毕，剩余'导师'={t.count('导师')}")

print("[B] Q4 复现包内的两份副本：")
apply(f"{AP}/论文Q4/复现包/recall/g1-audit-batch1.md", PAIRS_G1)
apply(f"{AP}/论文Q4/复现包/docs/s3-extraction-report.md", PAIRS_S3)
PYEOF
echo ""
echo "=== C) 复验（应为空） ==="
grep -rn '导师\|advisor' /mnt/f/文献/AgentOps/论文Q4/复现包 /mnt/f/文献/AgentOps/实验记录 --include='*.md' 2>/dev/null | head -6
echo "(无输出=干净)"
