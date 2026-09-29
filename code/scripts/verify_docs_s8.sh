#!/usr/bin/env bash
pkill -f 'grep -rn' 2>/dev/null; sleep 0.5
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
import os
AP = "/mnt/f/文献/AgentOps"

checks = {
  "整改计划 C2 完成": [f"{AP}/论文/审稿模拟/审稿汇总与整改计划.md", "完成（2026-09-29）"],
  "进度行 C2 完成": [f"{AP}/01-进度.md", "C2 完成（受控复跑）"],
  "进度行 合规": [f"{AP}/01-进度.md", "审计标签中性化"],
  "页脚更新": [f"{AP}/01-进度.md", "C2 真机 A≠M 完成（0% vs 10% 非法、−23.1%）"],
}
for name, (f, s) in checks.items():
    t = open(f, encoding="utf-8").read()
    print(f"  {name}: {'✓' if s in t else '✗ 未找到'}")

# 旧文件名引用（仅定向文件）
print("\n[旧文件名定向检查]")
files = [f"{AP}/01-进度.md", f"{AP}/论文/Paper1-draft-v2.md", f"{AP}/论文/审稿模拟/审稿汇总与整改计划.md",
         f"{AP}/论文Q4/复现包/MAPPING.md", f"{AP}/论文Q4/12-签字单.md", f"{AP}/论文Q4/复现包/SIGNOFF.md"]
for f in files:
    if not os.path.exists(f):
        print(f"  (missing) {f}")
        continue
    t = open(f, encoding="utf-8").read()
    n1, n2 = t.count("导师复核意见"), t.count("advisor-review")
    print(f"  {f.split('AgentOps/')[-1]}: 导师复核意见={n1} advisor-review={n2}")
PYEOF
echo ""
echo "[删除草稿 + 目录清点]"
rm -f '/mnt/f/文献/AgentOps/论文/latex/s8_paragraph_draft.md' && echo "  草稿已删除"
ls '/mnt/f/文献/AgentOps/论文/latex/'
