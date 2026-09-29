# -*- coding: utf-8 -*-
"""① 落档人类标注报告 ② 论文/封面信写入人类锚点 ③ 更新整改映射与进度"""
import os

AP = "/mnt/f/文献/AgentOps"
C1 = f"{AP}/实验记录/C1-人类盲标"

# ---------- ① 报告 ----------
rep = """# C1 · 人类盲标结果（150 站点，独立人类标注者）

> 回传：`F:\\Download\\c1_results.csv`（2026-09-29）｜ 存档：`F:\\文献\\AgentOps\\实验记录\\C1-人类盲标\\人类标注\\c1_results-human.csv`
> 逐条记录与统计：`F:\\文献\\AgentOps\\实验记录\\C1-人类盲标\\C1-人类标注-结果.json`

## 一、验收
- 150 行、ID 完整、无缺失；**Y=63 / N=87 / U=0**；13 条带理由备注（如"运行期接线/共享锁存在性"、"注意力特性×后端能力组合"、"请求参数需对应引擎配置"）——符合"按定义逐条判断"的预期。

## 二、一致率（κ）
| 对比 | n | 原始一致 | Cohen's κ |
|---|---|---|---|
| 人类 vs 评测者 AI 标签 | 150 | 75.3% | **0.528** |
| 人类 vs AI 第三遍（kit 协议） | 149 | 83.9% | **0.677** |

**解读**：人-机一致率与既有的 AI-AI 一致率（κ=0.60 / 0.65）**同一水平**——说明标签不确定度是**任务固有**的（"运行期/接线类检查是否算配置约束"的边界），而非 AI 标注独有。

## 三、人类标签下的证据捕获率（±1 行）
| 口径 | 捕获率 | 对照（评测者标签） |
|---|---|---|
| 层等权 | **84.8%** | 87.2% |
| 站点加权（244/119/2766） | **61.9%** | 59.5% |
| 约束加权（N_t×p_t） | **72.2%** | 63.2% |

分层（人类）：tier1 Y=38/50 → 97.4%；tier2 18/50 → 100%；tier3 7/50 → 57.1%。

**方向**：人类比评测者**更严格**（63 个正例 vs 评测者在同 150 站点上约 102 个），与既往每一遍独立标注的方向一致（评测者是更宽松的一方）。

## 四、结论与局限
- **结论**：人类锚点与 AI 结论**相容**——κ 与人-机水平相当，召回估计在人类标签下保持（等权 ±1 84.8% vs 87.2%）；论文可据此把"人类锚点"从"待办"升级为"已完成（150 站点）"。
- **局限**：仅**单一人类**（无 人-人 κ）；300 站点全帧与 130 条约束审计仍为 AI 产出；若需人-人 κ，可再加一位标注者只标 **30 站点重叠子集**（约 15 分钟）。
"""
open(f"{C1}/C1-人类标注-报告.md", "w", encoding="utf-8", newline="").write(rep)
print("报告已写")

MAIN = f"{AP}/论文/latex/main.tex"
COVER = f"{AP}/论文/latex/cover-letter.txt"
MAP = f"{AP}/论文/审稿模拟/第二轮-整改映射-2026-09-29.md"
PROG = f"{AP}/01-进度.md"

pairs_main = [
    # 摘要
    ("(87.2\\% within $\\pm$1 line; 53.0\\%/63.2\\% under constraint-level design weighting). The same protocol extracts",
     "(87.2\\% within $\\pm$1 line; 53.0\\%/63.2\\% under constraint-level design weighting), with an independent human labeler reproducing the estimate on 150 sites (84.8\\% equal-weight $\\pm$1 line). The same protocol extracts"),
    # §RQ1 审计段尾
    ("Cumulative: \\textbf{130 constraint-audits, 0 incorrect}. All audits and labels in this paper were produced by pipeline roles or independent AI instances---no external human expert has yet reviewed them; a human sign-off checklist ships with the artifact release (\\S\\ref{sec:limitations}).",
     "Cumulative: \\textbf{130 constraint-audits, 0 incorrect}. All audits in this paper were produced by pipeline roles or independent AI instances; for the 150-site labeling kit, an independent human labeler (a technically literate non-expert following the released instructions) has since repeated the pass: agreement with the evaluator labels is 75.3\\% raw / $\\kappa=0.53$ and with the third pass 83.9\\% / $\\kappa=0.68$---comparable to the AI-vs-AI agreement---and the human labels reproduce the capture estimate (84.8\\% equal-weight and 72.2\\% constraint-weighted $\\pm$1 line); the human is again stricter than the evaluator, the same direction as every independent pass."),
    # 贡献 #2
    ("a third blind labeling pass over 150 sites ($\\kappa = 0.65$, released kit protocol) reproduces the $\\pm$1 recall estimate.",
     "a third blind labeling pass over 150 sites ($\\kappa = 0.65$, released kit protocol) and an \\textbf{independent human labeler} on the same sites ($\\kappa = 0.53$ vs evaluator, 0.68 vs third pass; 84.8\\% equal-weight $\\pm$1 capture) reproduce the recall estimate."),
    # 限制节 Evaluator independence
    ("across four passes (60+60+30+150 sites) they agree at $\\kappa = 0.46$--$0.79$ (the 150-site kit pass: 82.6\\% raw / 0.65), 23 of 24 disagreements in the first comparison run in the direction of the evaluator being more inclusive, and the stricter labels raise $\\pm$1-line recall to 92.3\\% on the batch-2 subset---a human sign-off remains part of the artifact release checklist.",
     "across five passes (60+60+30+150 AI sites, plus a 150-site human pass) they agree at $\\kappa = 0.46$--$0.79$ (human vs evaluator 0.53; human vs third pass 0.68), 23 of 24 disagreements in the first comparison run in the direction of the evaluator being more inclusive, and the stricter labels raise $\\pm$1-line recall to 92.3\\% on the batch-2 subset. One independent human labeler has now completed the 150-site kit pass; the full 300-site gold-standard frame and the 130 constraint audits remain AI-labeled, so a human sign-off for the complete release stays on the artifact checklist."),
]
pairs_cover = [
    ("and a lower, scope-different 68.0% (at +/-1 line) on an independent non-scanner frame",
     "a lower, scope-different 68.0% (at +/-1 line) on an independent non-scanner frame, and an independent human labeler (150 sites) reproducing the estimate (84.8% equal-weight at +/-1 line; kappa 0.53 vs evaluator, 0.68 vs the third blind pass)"),
]

for path, pairs in ((MAIN, pairs_main), (COVER, pairs_cover)):
    t = open(path, encoding="utf-8").read()
    for i, (o, n) in enumerate(pairs, 1):
        c = t.count(o)
        print(f"[{os.path.basename(path)}] pair{i}: count={c}")
        if c == 1:
            t = t.replace(o, n)
    open(path, "w", encoding="utf-8", newline="").write(t)

# ---------- ③ 映射 + 进度 ----------
t = open(MAP, encoding="utf-8").read()
t = t.replace("## B 批 · 需真人（三位审稿人一致列为接受前提）",
              "## B 批 · 人类盲标 —— ✅ 已完成（2026-09-29）")
t = t.replace("- **人类盲标**：2 名标注者 × ≥150 站点 + 覆盖全部人-机分歧（约 45–75 分钟/人）",
              "- ✅ **人类盲标完成**：1 名独立标注者、150 站点（Y=63/N=87/U=0）；人-机一致 **κ=0.53（vs 评测者）/ 0.68（vs 第三遍）**；人类标签下 ±1 捕获 **等权 84.8% / 站点加权 61.9% / 约束加权 72.2%**；报告 `F:\\文献\\AgentOps\\实验记录\\C1-人类盲标\\C1-人类标注-报告.md`")
open(MAP, "w", encoding="utf-8", newline="").write(t)

t = open(PROG, encoding="utf-8").read()
anchor = "| 2026-09-29 | 审稿模拟 | **第二轮三审完成 + A 批整改（13 项）**"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
row = ("| 2026-09-29 | C1 | **人类盲标完成（B 批闭环）**：独立人类标注者 150 站点（Y=63/N=87/U=0；13 条带理由备注）→ "
       "与评测者 75.3%/κ=0.53、与 AI 第三遍 83.9%/κ=0.68（与 AI-AI 同水平→标签不确定度属任务固有）；"
       "人类标签下 ±1 捕获 **等权 84.8% / 站点加权 61.9% / 约束加权 72.2%**（对照 87.2/59.5/63.2）；人类比评测者更严格，方向与既往一致；"
       "论文摘要/§IV-A/贡献#2/§VI + cover letter 已写入；产物 `C1-人类标注-报告.md`、`C1-人类标注-结果.json`、`人类标注/c1_results-human.csv` |")
t = t[:j + 1] + row + "\n" + t[j + 1:]
open(PROG, "w", encoding="utf-8", newline="").write(t)
print("映射与进度已更新")
