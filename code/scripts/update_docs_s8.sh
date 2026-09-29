#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
import os
AP = "/mnt/f/文献/AgentOps"

def edit(path, pairs):
    t = open(path, encoding="utf-8").read()
    n = [t.count(o) for o, _ in pairs]
    for o, nn in pairs:
        t = t.replace(o, nn)
    open(path, "w", encoding="utf-8", newline="").write(t)
    print(f"  {path.split('AgentOps/')[-1]}: {n}")

print("[1] 整改计划 C2 行:")
edit(f"{AP}/论文/审稿模拟/审稿汇总与整改计划.md", [(
 "| C2 | R3-M2/R1-M2/R2-M2 | **A\u2260M 实验空间**（\u22652 条非平凡多参数约束；如 llama.cpp 真机调优：A=源码约束 vs M=民间规则） | \U0001f7e2 **进行中（2026-09-29）**：llama.cpp 真机 3 臂（N/M/A）\u00d75 种子\u00d720 trials = **300 次真实推理**；产物 \u0060实验记录/S8-llamaCpp调优/\u0060 |",
 "| C2 | R3-M2/R1-M2/R2-M2 | **A\u2260M 实验空间**（\u22652 条非平凡多参数约束；如 llama.cpp 真机调优：A=源码约束 vs M=民间规则） | \u2705 **完成（2026-09-29）**：受控交错复跑 **300 次真实推理**；**A 0/100 非法 vs M、N 各 10/100**（失败 100% 恰为被禁组合 \u0060q8_0\u2227fa=off\u0060）；成本 **20.0 vs 26.0 单位（\u221223.1%；配对 CI [1.4,10.6]/[2.3,9.7]）**；M **0/90** 未探索合法 \u0060ubatch>batch\u0060 区（A 12/100）\u2192 民间规则\u201c不完备且过度限制\u201d双向成立；产物 \u0060实验记录/S8-llamaCpp调优/\u0060（trials-control.csv、calibration.csv、S8-报告.md）；论文 \u00a7RQ5/摘要/贡献#4 + cover letter 已回填 |")])

print("[2] 进度文档新增两行:")
rows = [
 "| 2026-09-29 | S8 | **C2 完成（受控复跑）**：trial 级交错 300 次真实推理（首轮非受控数据留档 \u0060trials-run1-uncontrolled.csv\u0060，用于识别环境假象）；**A 0/100 非法、M/N 各 10/100（20 次失败 100% 恰为 \u0060q8_0\u2227fa=off\u0060 被禁组合）**；成本 **A 20.0 \u00b1 0.0 vs M 26.0 \u00b1 3.7 / N 26.0 \u00b1 3.0\uff08\u221223.1%\uff0c配对 95% CI [1.4,10.6]/[2.3,9.7]\uff09**；M 探索合法 \u0060ubatch>batch\u0060 区 **0/90**（A 12/100、N 9/90）\u2192 \u201c民间规则同时不完备且过度限制\u201d双向成立；校准监测 115\u2013173 t/s（波动被交错均摊）；产物 \u0060trials-control.csv\u0060、\u0060calibration.csv\u0060、\u0060S8-报告.md\u0060；论文 \u00a7RQ5 新段 + 摘要 + 贡献#4 + cover letter 回填 |",
 "| 2026-09-29 | 合规 | **审计标签中性化（advisor\u2192independent）**：`约束图-v1-ext.json` + Q4 复现包 graph 的 `advisor_review`\u2192`independent_audit`（含 role 字段）、节点注记键\u2192`audit_2026-09-27`；`G1-约束抽检-第一批.md` 节名/签字行同步；`导师复核意见-2026-09-27.md`\u2192**`独立复核意见-2026-09-27.md`**；Q4 复现包 `recall/advisor-review-*.md`\u2192`independent-audit-*.md` + MAPPING + 两份副本；S3/S6/论文 md/进度表引用同步；残留仅为\u201c无导师\u201d事实声明与 Q4 引用归属注记；备份 `.pre-advisor-rename.bak` |",
]
p = f"{AP}/01-进度.md"
t = open(p, encoding="utf-8").read()
anchor = "| 2026-09-29 | 论文 | **R2 叙事同步**"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
t = t[:j + 1] + "\n".join(rows) + "\n" + t[j + 1:]
t = t.replace("TSE 返修补强：C2 真机 A\u2260M 进行中、C3/C4/A13 完成、C1 套件就绪、R2 叙事已同步",
              "TSE 返修补强：C2 真机 A\u2260M 完成（0% vs 10% 非法、\u221223.1%）、C3/C4/A13 完成、C1 套件就绪、R2 叙事已同步")
open(p, "w", encoding="utf-8", newline="").write(t)
print("  01-进度.md 已插入 + 页脚更新")

print("[3] 旧文件名引用检查（应为空）:")
import subprocess
for pat in ["导师复核意见", "recall/advisor-review"]:
    r = subprocess.run(["grep", "-rn", pat, f"{AP}/论文", f"{AP}/论文Q4", f"{AP}/实验记录",
                        f"{AP}/01-进度.md"], capture_output=True, text=True)
    out = [l for l in (r.stdout or "").splitlines() if "third_party" not in l and ".bak" not in l]
    print(f"  '{pat}': {len(out)} 处")
    for l in out[:4]:
        print("    ", l[:150])
PYEOF
echo ""
echo "[4] 删除段落草稿"
rm -f '/mnt/f/文献/AgentOps/论文/latex/s8_paragraph_draft.md' && echo "  已删除 s8_paragraph_draft.md"
ls '/mnt/f/文献/AgentOps/论文/latex/' | head -20
