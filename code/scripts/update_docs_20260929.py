# -*- coding: utf-8 -*-
"""更新两份管理文档：审稿整改计划（A13/B5/C1-C4 状态）+ 01-进度.md（本轮 6 行 + 页脚）"""
import io

PLAN = "/mnt/f/文献/AgentOps/论文/审稿模拟/审稿汇总与整改计划.md"
PROG = "/mnt/f/文献/AgentOps/01-进度.md"

pairs = [
    ("| A13 | R3-11 | 产物元数据 4 处错误（SGLang meta 引用 vLLM commit；ext 图 stats.total=282；P2 flags 259 vs 262；S6 报告 165.4 vs 159.77） | 修产物文件 |",
     "| A13 | R3-11 | 产物元数据 4 处错误（SGLang meta 引用 vLLM commit；ext 图 stats.total=282；P2 flags 259 vs 262；S6 报告 165.4 vs 159.77） | ✅ 已修（2026-09-29）：SGLang 3 文件 commit→\u006094602c9\u2026\u0060（GitHub API 核验）；ext stats.total→716（重算 by_type/by_scope）；版本对比注\u201c259 去重/262 注册\u201d；S6 首页→159.77（5-rep 主口径）；论文措辞同步；均留 \u0060.pre-a13-20260929.bak\u0060 |"),
    ("| B5 | R2-M6 | 制品-正文不一致 | 随 A13 一并修 |",
     "| B5 | R2-M6 | 制品-正文不一致 | ✅ 随 A13 修毕（2026-09-29） |"),
    ("| C1 | R3-M3/R1-M3/R2-M5 | **人类**盲标/盲审（≥100 节点或 150\u2013300 站点） | \u26a0\ufe0f 需人工（用户侧） |",
     "| C1 | R3-M3/R1-M3/R2-M5 | **人类**盲标/盲审（≥100 节点或 150\u2013300 站点） | \U0001f7e1 **套件就绪（2026-09-29）**：\u0060实验记录/C1-人类盲标/\u0060（离线 HTML 工具 + 说明 + 导入脚本；150 站点分层 50/50/50；合成数据自测通过）；**待一人 45\u201375 分钟**，回传 CSV 即自动出 \u03ba/召回 |"),
    ("| C2 | R3-M2/R1-M2/R2-M2 | **A\u2260M 实验空间**（≥2 条非平凡多参数约束；如 llama.cpp 真机调优：A=源码约束 vs M=民间规则） | \u26a0\ufe0f 可做（建议返修期或投稿前） |",
     "| C2 | R3-M2/R1-M2/R2-M2 | **A\u2260M 实验空间**（≥2 条非平凡多参数约束；如 llama.cpp 真机调优：A=源码约束 vs M=民间规则） | \U0001f7e2 **进行中（2026-09-29）**：llama.cpp 真机 3 臂（N/M/A）\u00d75 种子\u00d720 trials = **300 次真实推理**；产物 \u0060实验记录/S8-llamaCpp调优/\u0060 |"),
    ("| C3 | R1-M5 | 相关工作补漏（审稿人给出的具体清单待读全文） | 见原报告 |",
     "| C3 | R1-M5 | 相关工作补漏（审稿人给出的具体清单待读全文） | ✅ **完成（2026-09-29）**：补 ConfInLog（ICPC\u201921，Shu-Lin Zhou et al.，S2 核验）+ Pimp My LLM（arXiv:2602.17697，API 核验）；cDep 转述更正；Ciri 作者更正；\u201c3 vs 716\u201d 与覆盖率口径限定；main.tex 重编译 10 页 0 Overfull |"),
    ("| C4 | R3-M1 | 独立于扫描器的抽样框（模块级人工通读） | 返修期 |",
     "| C4 | R3-M1 | 独立于扫描器的抽样框（模块级人工通读） | ✅ **完成（2026-09-29）**：独立 AST 抽样框（150/2,479 文件；强候选 98 \u2192 人工裁定 50 引擎站点）\u2192 捕获率 **68.0% [54.2, 79.2]**（与候选池口径 71.9% 吻合）；论文 \u00a7RQ1 + 贡献 2 + \u00a7Limitations 已回填；产物 \u0060实验记录/C4-独立抽样框/\u0060 |"),
    ("2. **强烈建议**（决定投稿质量）：C1 找人做 llama.cpp",  # 占位保护（若不存在则忽略）
     "2. **强烈建议**（决定投稿质量）：C1 找人做 llama.cpp"),
]
pairs = pairs[:-1]

t = open(PLAN, encoding="utf-8").read()
for old, new in pairs:
    c = t.count(old)
    print(f"plan count={c}: {old[:40]}\u2026")
    if c == 1:
        t = t.replace(old, new)
open(PLAN, "w", encoding="utf-8", newline="").write(t)

# 建议段更新
old2 = "2. **强烈建议**（决定投稿质量）：C1 找人做人类盲标（~2 天）；C2 做 llama.cpp 真机 A\u2260M 实验（~2\u20133 天）；"
new2 = "2. **进度更新（2026-09-29）**：C2 真机 A\u2260M 实验**进行中**（llama.cpp，300 次真实推理）；C3/A13/C4 **已完成**；C1 套件已就绪\u2014\u2014**只需一人 45\u201375 分钟**完成 150 站点盲标（\u0060实验记录/C1-人类盲标/\u0060），回传 CSV 即自动出统计；"
t = open(PLAN, encoding="utf-8").read()
c = t.count(old2)
print("plan 建议段 count=", c)
if c == 1:
    t = t.replace(old2, new2)
    open(PLAN, "w", encoding="utf-8", newline="").write(t)

# ---------- 进度文档 ----------
rows = [
    "| 2026-09-29 | 审稿模拟 | **C3 完成**：补 ConfInLog（ICPC\u201921，Shu-Lin Zhou et al.，SemanticScholar 核验）+ **Pimp My LLM**（arXiv:2602.17697，arXiv API 核验）两条文献；更正 cDep 转述（\u201ccritique 既有 NLP 工作\u201d而非\u201ccalls for\u201d）、Ciri 作者名单、SCOOT \u201c3 vs 716\u201d 口径与覆盖率限定；main.tex 重编译（10 页，0 Overfull） |",
    "| 2026-09-29 | 审稿模拟 | **A13 完成（4/4）**：SGLang 图/参数文件 + Q4 复现包 meta.commit 更正为 **94602c9c\u2026**（v0.5.20 tag，GitHub API 核验；原为 vLLM 提交号误填）；ext 图 stats.total 282\u2192716（重算 by_type/by_scope + tiers 拆分）；版本对比.md 注明 **259 去重 / 262 注册**；S6 报告首页 165.4\u2192159.77（5-rep 主口径）；全部留 \u0060.pre-a13-20260929.bak\u0060 |",
    "| 2026-09-29 | 审稿模拟 | **C4 完成**：非扫描器独立抽样框（150/2,479 文件，种子 20260929；独立 AST 枚举 + 名称表预筛 + 逐条裁定）\u2192 50 引擎配置站点中捕获 **34 = 68.0%（Wilson 95% CI [54.2, 79.2]；精确同行 24）**，与候选池口径 71.9% 吻合；未捕获集中于注意力后端量化组合、molmo TP 整除、运行期模块（DP/hisparse）；论文 \u00a7RQ1 新增段落 + 贡献 2 + \u00a7Limitations 回填；产物 \u0060实验记录/C4-独立抽样框/\u0060 |",
    "| 2026-09-29 | 审稿模拟 | **C1 套件就绪**：\u0060实验记录/C1-人类盲标/\u0060（离线 HTML 标注工具 + 说明 + 导入脚本；150 站点（两批金标准各 75，tier 50/50/50）；合成数据端到端自测通过 \u03ba/召回链路）；**待一人 45\u201375 分钟**盲标后回传 CSV |",
    "| 2026-09-29 | S8 | **C2 启动（真机 A\u2260M）**：llama.cpp v0.5.0 三臂（N 无约束 / M 民间规则 \u201cubatch\u2264batch\u201d（已证伪）/ A 源码约束 \u201cq8_0\u21d2fa=on\u201d）\u00d7 5 种子 \u00d7 20 trials = **300 次真实推理**；空间 threads{2,3,4}\u00d7batch{128,256,512}\u00d7ubatch{64,128,256}\u00d7fa{on,off}\u00d7ctv{f16,q8_0}=108 组合；成本 成功 1 / 失败 1+3；冒烟与失败路径（rc=1）已验；产物 \u0060实验记录/S8-llamaCpp调优/\u0060 |",
    "| 2026-09-29 | 论文 | **R2 叙事同步**：\u0060Paper1-draft-v2.md\u0060 9 处过时表述（\u201c过度断言/从未成立\u201d）改为\u201c衰减\u201d叙事并补运行时守卫复核方法句；\u0060scoot-drift.json\u0060 增 \u0060correction_2026_09_29\u0060 更正块（含受影响产物清单） |",
]

t = open(PROG, encoding="utf-8").read()
anchor = "| 2026-09-28 | Q4 | **Q4 全文初稿 + 图表 + 内部审稿（第一轮）完成**"
i = t.find(anchor)
assert i > 0, "anchor not found"
j = t.find("\n", i)
insert = "\n".join(rows)
t = t[:j + 1] + insert + "\n" + t[j + 1:]
old_f = "*最后更新：2026-09-28（Q4 论文："
new_f = "*最后更新：2026-09-29（TSE 返修补强：C2 真机 A\u2260M 进行中、C3/C4/A13 完成、C1 套件就绪、R2 叙事已同步；Q4 论文："
assert t.count(old_f) == 1
t = t.replace(old_f, new_f)
open(PROG, "w", encoding="utf-8", newline="").write(t)
print("progress 已插入", len(rows), "行 + 页脚更新")
