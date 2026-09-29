# -*- coding: utf-8 -*-
"""① 摘要压到 ≤200 词 ② 附录→正文小节 ③ 同步提交清单（单盲确认 + 格式项）"""
import re

MAIN = "/mnt/f/文献/AgentOps/论文/latex/main.tex"
OUT = "/mnt/f/文献/AgentOps/论文/latex/投稿-提交清单.md"

NEW_ABS = ("Hand-written configuration knowledge does not last: of the three ``known constraints'' a production tuner "
 "(SCOOT) ships, audited release by release at source and execution level, one was removed upstream, one is now dormant "
 "under changed defaults, and six of six tested folk rules are unenforced on a second engine. We present "
 "\\textbf{VeriCon}: it mines parameter constraints from engine source with LLM agents (verbatim \\code{file:line} "
 "evidence each), \\emph{falsifies} them by executing the engine's real validation path on violating configurations "
 "(no GPU), and injects the verified set into a Bayesian tuner. On vLLM v0.30.0 it extracts \\textbf{716} constraints, "
 "confirms \\textbf{113} via the construction path, and measures \\textbf{71.9\\%} recall (87.2\\% at $\\pm$1 line; "
 "\\textbf{84.8\\%} equal-weight under an independent human labeler; 53.0\\%/63.2\\% design-weighted); on SGLang "
 "v0.5.20, \\textbf{420}. Across 8{,}000+ simulated trials, constraint injection cuts tuning cost by "
 "\\textbf{43.5--50.9\\%}; the manual and mined arms coincide by construction in that subspace, so this isolates the "
 "value of constraint \\emph{knowledge}---\\emph{automatic extraction}'s value is established in RQ1--RQ4 and on the "
 "real engine. A 400-trial llama.cpp micro-study separates the sources: \\textbf{0\\%} invalid trials for source-mined "
 "constraints vs \\textbf{5\\%} (online learning), \\textbf{12\\%} (folk rule), \\textbf{17\\%} (none), at "
 "\\textbf{13--34\\% lower cost}---all on a four-core laptop at zero cash cost.")

tex = open(MAIN, encoding="utf-8").read()

def count_words(latex):
    s = latex
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\emph\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\code\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\%", "%", s)
    s = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{[^{}]*\})?", " ", s)
    s = re.sub(r"[{}$\\]", " ", s)
    return len([w for w in s.replace("~", " ").split() if any(c.isalnum() for c in w)])

lines = tex.splitlines()
i = next(k for k, l in enumerate(lines) if l.strip() == r"\begin{abstract}")
lines[i + 1] = NEW_ABS
tex = "\n".join(lines) + "\n"
print("新摘要词数（正确口径）:", count_words(NEW_ABS))

# 附录→正文小节
old_app = "\\appendix\n\\section{Artifact Availability}"
assert tex.count(old_app) == 1
tex = tex.replace(old_app, "\\section{Artifact Availability}")
tex = tex.replace("released (Appendix~\\ref{app:artifact})", "released (\\S\\ref{app:artifact})")
open(MAIN, "w", encoding="utf-8", newline="").write(tex)
print("附录已转为正文小节；引用已改为 § 引用")

# 同步提交清单
def plain(s):
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\emph\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\code\{([^{}]*)\}", r"\1", s)
    s = s.replace("\\%", "%").replace("``", '"').replace("''", '"')
    s = s.replace("---", " - ").replace("--", "-").replace("$\\pm$", "+/-")
    s = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}$\\]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

txt = open(OUT, encoding="utf-8").read()
txt = re.sub(r"(?s)(\*\*Abstract\*\*（纯文本，直接粘贴）\n```\n).*?(\n```)",
             lambda m: m.group(1) + plain(NEW_ABS) + m.group(2), txt, count=1)
# 更新第 3 节：单盲已确认 + 格式项
txt = txt.replace(
 "## 3) 需要你本人确认的三件事（我不能代做）",
 "## 3) 已核实与注意事项（2026-09-29 查证 IEEE CS 作者指南）\n\n- ✅ **评审模式：单盲（single-anonymous）**——TSE 明确\"不提供 double-anonymous 选项\"，**保持作者信息即可，无需匿名版**。\n- ✅ **摘要 ≤200 词**（CS 规定常规论文 100–200 词）：当前 **198 词**，合规。\n- ✅ **附录须作 supplemental 单独提交**：已将原 `Appendix` 改为正文小节 \"Artifact Availability\"，无需另传补充文件。\n- ℹ️ **ORCID 必填**（ScholarOne 会要求）。\n- ℹ️ **关键词建议从 ScholarOne 的 ACM 分类表选择**（我们的自由文本关键词可作参考）。\n- ℹ️ **页数**：11 页 < 12 页上限，无超页费。\n- ℹ️ CS 有**预筛**（范围/格式/可读性）——我们符合。\n\n## 3b) 需要你本人确认的事项（我不能代做）")
open(OUT, "w", encoding="utf-8", newline="").write(txt)
print("清单已更新")
