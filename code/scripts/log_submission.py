# -*- coding: utf-8 -*-
"""登记 TSE 投稿成功（进度表 + 投稿确认存档）"""
import os

AP = "/mnt/f/文献/AgentOps"
LAT = f"{AP}/论文/latex"

confirm = """# TSE 投稿确认（2026-09-30）

| 项 | 内容 |
|---|---|
| 期刊 | **IEEE Transactions on Software Engineering**（IEEE；期刊，非会议） |
| 投稿系统 | **IEEE Author Portal**（Atypon ReX），site `tse-cs` |
| 状态 | **Submitted**（面板原文：Submission Status: Submitted；"This submission has been sent to the editorial office"） |
| 提交时间 | **30 September 2026**（开始 29 September 2026） |
| 作者 | Shuheng Zhao（Mr.；zshbdfdc@163.com；China；Independent Researcher；ORCID 已链接 0009-0002-3357-5532） |
| Article Type | Regular (Journal First)（= 常规期刊投稿；非会议扩展版） |
| 稿件文件 | ① `tse-latex-bundle.zip`（Main Document - LaTeX，320.4 KB）② `main-final.pdf`（Main Document - PDF，406 KB）③ `cover-letter.pdf`（Cover letter / Comments，42.9 KB） |
| 关键词（ACM） | D.2.16 Configuration Management；D.2.4 Software/Program Verification；C.4 Performance of Systems；G.1.6 Optimization；I.2.7 Natural Language Processing；I.2.6 Learning |
| SE 任务 | Managing the development and runtime environment（含 configuration management）；Verification, validation, assurance |
| 研究方法 | Empirical；Analytical；Constructive |
| 工具/技术 | Foundation Models；Static program analysis；Dynamic program analysis；Statistical methods |
| 资助 | No funding was received for this research |
| 代码/数据 | 投稿时无可共享仓库（No）；论文声明复现包随论文发布 |
| 既往发表 | 未投过本刊；从未发表/展示过（无会议扩展） |
| 受试者 | 无人类受试者；无动物受试者 |
| Submission Board ID | `1509691a-4b01-4ed5-a311-9c6ad251a1e3` |

## 过程中避开的三处坑（实测记录）
1. `mc.manuscriptcentral.com/tse` = 牛津大学出版社《**Transportation Safety and Environment**》（缩写同为 TSE）——**投错期刊**，已弃用该草稿（未提交，无影响）。
2. `mc.manuscriptcentral.com/tse-cs` = IEEE TSE 的 ScholarOne，但页面明示 "**This site is no longer used for new submissions** … only accepts invited submissions" → 新投稿必须走 **IEEE Author Portal**。
3. Main Manuscript 槽位要求 **MS Word 或 LaTeX**，并额外要求一份 **PDF 版正文**（`Main Document - PDF`）；已同时提交 LaTeX 打包件与编译好的 PDF。

## 后续
- 等待编辑部/ ScholarOne 确认邮件（含 **Manuscript ID**）；收到后登记进 `01-进度.md`。
- 进入评审后若收到返修：C 批可选项（真实 GPU / vLLM V1 端到端锚点）届时再补。
"""
open(f"{LAT}/投稿-提交确认.md", "w", encoding="utf-8", newline="").write(confirm)
print("已写:", f"{LAT}/投稿-提交确认.md")

p = f"{AP}/01-进度.md"
t = open(p, encoding="utf-8").read()
anchor = "| 2026-09-29 | 投稿 | **发射前核查（IEEE CS 作者指南查证）**"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
row = ("| 2026-09-30 | 投稿 | **✅ 已投稿 TSE（IEEE Author Portal / Atypon ReX，site tse-cs）**：状态 **Submitted**（30 Sep 2026 by Shuheng Zhao）；"
       "类型 **Regular (Journal First)**；文件 = LaTeX 打包件（Main Document - LaTeX）+ `main-final.pdf`（Main Document - PDF）+ `cover-letter.pdf`（Cover letter / Comments）；"
       "ACM 关键词 6 个（D.2.16 配置管理、D.2.4 程序验证、C.4 系统性能、G.1.6 优化、I.2.7 NLP、I.2.6 学习）、SE 任务 2 项、方法 3 项、工具 4 项；"
       "作者 Mr./zshbdfdc@163.com/China/Independent Researcher，ORCID 已链接；无资助、无代码数据仓库、未投过本刊、无受试者；"
       "Board ID `1509691a-4b01-4ed5-a311-9c6ad251a1e3`；确认存档 `论文/latex/投稿-提交确认.md`。"
       "**避开的坑**：`mc.manuscriptcentral.com/tse` 是牛津《Transportation Safety and Environment》（同名缩写，投错期刊）；"
       "`tse-cs` ScholarOne 已停新投稿（仅邀请稿）→ 必须走 Author Portal；主稿件槽需 LaTeX/Word + 单独 PDF 版 |")
t = t[:j + 1] + row + "\n" + t[j + 1:]
open(p, "w", encoding="utf-8", newline="").write(t)
print("进度已登记")
