# -*- coding: utf-8 -*-
"""① 标注旧 main.pdf ② 提交清单指向 main-final.pdf ③ 进度登记（单盲查证 + 摘要 200 词 + 附录改节）"""
import os

LAT = "/mnt/f/文献/AgentOps/论文/latex"

note = """投稿用文件说明（2026-09-29）
================================

**投稿请上传：main-final.pdf**（最终版：11 页、199 词摘要、无附录、0 未定义引用）

- `main-final.pdf` —— ✅ **最终投稿版**（2026-09-29 12:35 构建）
- `main.pdf` —— ⚠️ **旧版**（11:47，218 词摘要 + 附录版），因被 PDF 预览占用无法覆盖；
  关闭预览后可以删掉它，避免误传。两者差异：摘要更短（≤200 词，符合 IEEE CS 规定）、
  原"Appendix"已改为正文小节 "VIII. ARTIFACT AVAILABILITY"（CS 规定附录须作 supplemental 单独提交）。

源文件：`main.tex`（权威）；编译脚本：`F:\\文献\\AgentOps\\代码\\scripts\\compile_with_texlive.sh`
"""
open(f"{LAT}/投稿用哪个文件-README.txt", "w", encoding="utf-8", newline="").write(note)

t = open(f"{LAT}/投稿-提交清单.md", encoding="utf-8").read()
t = t.replace("**Manuscript**：上传 `F:\\文献\\AgentOps\\论文\\latex\\main.pdf`",
              "**Manuscript**：上传 `F:\\文献\\AgentOps\\论文\\latex\\main-final.pdf`（最终版；`main.pdf` 是旧版，勿传）")
t = t.replace("- 稿件：`F:\\文献\\AgentOps\\论文\\latex\\main.pdf` —",
              "- 稿件：`F:\\文献\\AgentOps\\论文\\latex\\main-final.pdf` —")
open(f"{LAT}/投稿-提交清单.md", "w", encoding="utf-8", newline="").write(t)
print("清单与 README 已更新")

# 进度登记
p = "/mnt/f/文献/AgentOps/01-进度.md"
t = open(p, encoding="utf-8").read()
anchor = "| 2026-09-29 | C1 | **人类盲标完成（B 批闭环）**"
i = t.find(anchor)
assert i > 0
j = t.find("\n", i)
row = ("| 2026-09-29 | 投稿 | **发射前核查（IEEE CS 作者指南查证）**：**TSE = 单盲（single-anonymous），明确不提供双盲**（保持作者信息，无需匿名版）；"
       "按 CS 规定**摘要压到 199 词（100–200 词上限）**；**原附录改为正文小节 VIII「ARTIFACT AVAILABILITY」**（CS 规定附录须作 supplemental 单独提交）；"
       "封面信 3 处措辞对齐；预检：11 页 < 12 页（无超页费）、34 字体全嵌入、0 超链接、0 未定义引用；"
       "产出 `投稿-提交清单.md`（含可粘贴字段）、最终版 **`main-final.pdf`**（旧 main.pdf 被预览锁定，已加 README 标注勿传） |")
t = t[:j + 1] + row + "\n" + t[j + 1:]
open(p, "w", encoding="utf-8", newline="").write(t)
print("进度已登记")
