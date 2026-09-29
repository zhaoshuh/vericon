#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
import os

AP = "/mnt/f/文献/AgentOps"

# 1) G1 最后残留
p = f"{AP}/实验记录/G1-约束抽检-第一批.md"
t = open(p, encoding="utf-8").read()
t = t.replace("**签字**：导师复核通过", "**签字**：独立复核通过")
open(p, "w", encoding="utf-8", newline="").write(t)
print("G1 剩余'导师':", t.count("导师"))

# 2) Q4 复现包 recall 文件改名 + 内容中性化
old_f = f"{AP}/论文Q4/复现包/recall/advisor-review-2026-09-27.md"
new_f = f"{AP}/论文Q4/复现包/recall/independent-audit-2026-09-27.md"
if os.path.exists(old_f):
    t = open(old_f, encoding="utf-8").read()
    t = t.replace("# 导师复核意见书", "# 独立复核意见书")
    t = t.replace("复核人：导师角色（应用户要求由 AI 扮演，最终仍需真实导师确认）",
                  "复核人：独立复核角色（AI 实例；非外部人员；本项目无学术导师参与）")
    t = t.replace("复核人：导师角色（AI 扮演）", "复核人：独立复核角色（AI 实例）")
    t = t.replace("含导师复核节", "含独立复核节")
    t = t.replace("导师", "独立复核")
    open(new_f, "w", encoding="utf-8", newline="").write(t)
    os.remove(old_f)
    print("recall 文件已改名；剩余'导师':", t.count("导师"))

# 3) MAPPING.md 左列
mp = f"{AP}/论文Q4/复现包/MAPPING.md"
t = open(mp, encoding="utf-8").read()
t = t.replace("recall/advisor-review-2026-09-27.md", "recall/independent-audit-2026-09-27.md")
open(mp, "w", encoding="utf-8", newline="").write(t)
print("MAPPING 剩余'advisor':", t.count("advisor"))
PYEOF
echo ""
echo "=== 复现包中全局再查 advisor/导师/advisor-review ==="
grep -rn 'advisor\|导师' '/mnt/f/文献/AgentOps/论文Q4/复现包/' --include='*.md' --include='*.json' --include='*.txt' --include='*.py' --include='*.sh' 2>/dev/null | head -8
echo "(无输出=干净)"
echo ""
echo "=== run2 进度快照 ==="
L=$(wc -l < '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/run2.log' 2>/dev/null)
echo "log lines: $L / ~330"
tail -1 '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/run2.log' | cut -c1-110
echo "--- calibration ---"
cat '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/calibration.csv' 2>/dev/null | tail -4
