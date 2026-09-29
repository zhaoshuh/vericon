#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
def edit(path, pairs):
    t = open(path, encoding="utf-8").read()
    n = [t.count(o) for o, _ in pairs]
    for o, nn in pairs:
        t = t.replace(o, nn)
    open(path, "w", encoding="utf-8", newline="").write(t)
    print(f"  {path.split('AgentOps/')[-1]}: {n}")

print("[1] 计划 C1 行:")
edit("/mnt/f/文献/AgentOps/论文/审稿模拟/审稿汇总与整改计划.md", [(
 "| C1 | R3-M3/R1-M3/R2-M5 | **人类**盲标/盲审（\u2265100 节点或 150\u2013300 站点） | \U0001f7e1 **套件就绪（2026-09-29）**：\u0060实验记录/C1-人类盲标/\u0060（离线 HTML 工具 + 说明 + 导入脚本；150 站点分层 50/50/50；合成数据自测通过）；**待一人 45\u201375 分钟**，回传 CSV 即自动出 \u03ba/召回 |",
 "| C1 | R3-M3/R1-M3/R2-M5 | **人类**盲标/盲审（\u2265100 节点或 150\u2013300 站点） | \u2705 **第三遍独立盲标完成（AI 实例，非人类；2026-09-29）**：3 个 fresh-context 实例按 kit 协议盲标 150 站点（仅站点材料）\u2192 **一致率 82.6% / \u03ba=0.653**（对照既有 pass 0.60）；更严格标签下 \u00b11 捕获 **88.3%（等权）/ 75.3%（加权）**；论文 \u00a7RQ1 / 贡献#2 / \u00a7Limitations 已回填；**人类版套件仍可复用（可选，一人 45\u201375 分钟）** |")])

print("[2] 计划建议段:")
edit("/mnt/f/文献/AgentOps/论文/审稿模拟/审稿汇总与整改计划.md", [(
 "2. **进度更新（2026-09-29）**：C2 真机 A\u2260M 实验**进行中**（llama.cpp，300 次真实推理）；C3/A13/C4 **已完成**；C1 套件已就绪\u2014\u2014**只需一人 45\u201375 分钟**完成 150 站点盲标（\u0060实验记录/C1-人类盲标/\u0060），回传 CSV 即自动出统计；",
 "2. **进度更新（2026-09-29 晚）**：C2/C3/C4/A13 **全部完成**；C1 已由**第三遍独立 AI 盲标**完成（\u03ba=0.65）\u2014\u2014若审稿坚持 human 口径，人类版套件可原样复用（一人 45\u201375 分钟，自动出同一套统计）；")])

print("[3] 进度文档:")
p = "/mnt/f/文献/AgentOps/01-进度.md"
t = open(p, encoding="utf-8").read()
anchor = "| 2026-09-29 | 合规 | **审计标签中性化"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
row = ("| 2026-09-29 | C1 | **第三遍独立盲标完成（AI 实例；用户决定不另找人类）**：3 个 fresh-context 实例按 kit 协议盲标 150 站点"
       "（仅站点材料、禁读任何标签）→ **82.6% 一致 / κ=0.653**（tier 92/73/82%；对照既有 pass 0.60）；更严格标签下 ±1 捕获"
       " **88.3%/75.3%**（等权/加权）→ 召回估计对标签严格度稳健；修正导入脚本一致率计算 bug（Y↔C 映射未生效，κ 由 −0.295 修正为 0.653）；"
       "产物 `c1_results.csv`、`C1-独立盲标-报告.md`、`C1-导入结果.json`；论文 §RQ1/贡献#2/§Limitations 回填；人类版套件仍可复用 |")
t = t[:j + 1] + row + "\n" + t[j + 1:]
t = t.replace("C1 套件就绪、R2 叙事已同步", "C1 第三遍盲标完成（κ=0.65；人类版可选）、R2 叙事已同步")
open(p, "w", encoding="utf-8", newline="").write(t)
print("  已插入 + 页脚更新")
PYEOF
echo ""
echo "=== 重编译 ==="
bash /mnt/f/文献/AgentOps/代码/scripts/compile_with_texlive.sh 2>&1 | grep -E '✅|警告|Overfull|pages|Undefined' | head -6
echo ""
LOG=/mnt/f/文献/AgentOps/论文/latex/main.log
echo -n "Overfull: "; grep -c 'Overfull' "$LOG" || true
echo -n "undefined: "; grep -c 'undefined' "$LOG" || true
grep -o 'Output written on main.pdf ([0-9]* pages' "$LOG" | head -1
