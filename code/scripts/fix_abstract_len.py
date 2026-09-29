# -*- coding: utf-8 -*-
"""修正摘要超词数问题：① 重写摘要（压缩到 ≤250）② 用"保留参数内容"的正确转换器计数 ③ 同步提交清单"""
import re

MAIN = "/mnt/f/文献/AgentOps/论文/latex/main.tex"
OUT = "/mnt/f/文献/AgentOps/论文/latex/投稿-提交清单.md"

NEW_ABS = ("Hand-written configuration knowledge does not last: of the three ``known constraints'' a production tuner "
 "(SCOOT) ships, audited release by release at source and execution level, one was removed upstream, one keeps its "
 "semantics but is rendered dormant by changed defaults, and six of six tested folk rules are unenforced on a second "
 "engine. We present \\textbf{VeriCon}: the pipeline mines parameter constraints from engine source with LLM agents "
 "(verbatim \\code{file:line} evidence per constraint), \\emph{falsifies} each candidate by executing the engine's real "
 "validation path on constructed violating configurations (no GPU), and injects the verified set into a Bayesian tuner. "
 "On vLLM v0.30.0 it extracts \\textbf{716} evidence-backed constraints, confirms \\textbf{113} via the construction path, "
 "and measures \\textbf{71.9\\%} recall (87.2\\% within $\\pm$1 line; 53.0\\%/63.2\\% under constraint-level design "
 "weighting; \\textbf{84.8\\%} equal-weight under an independent human labeler); on SGLang v0.5.20, \\textbf{420} "
 "constraints. Across 8{,}000+ simulated trials, constraint injection cuts tuning cost by \\textbf{43.5--50.9\\%} "
 "(headline 48.6\\%, CI [46.7, 50.0]); in that subspace the manual and mined arms coincide by construction, so this "
 "isolates the value of constraint \\emph{knowledge}---\\emph{automatic extraction}'s value is established in RQ1--RQ4 "
 "and on the real engine. A 400-trial llama.cpp micro-study separates the sources: \\textbf{0\\%} invalid trials for "
 "source-mined constraints vs \\textbf{5\\%} (online learning), \\textbf{12\\%} (folk rule), \\textbf{17\\%} (none), at "
 "\\textbf{13--34\\% lower cost}---all on a four-core CPU laptop at zero cash cost.")


def count_words(latex):
    """正确的 LaTeX 词数：保留命令参数内容，只删命令名与排版符号"""
    s = latex
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\emph\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\code\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\%", "%", s)
    s = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?(\{[^{}]*\})?", " ", s)
    s = re.sub(r"[{}$\\]", " ", s)
    s = s.replace("~", " ")
    return len([w for w in s.split() if any(c.isalnum() for c in w)])


lines = open(MAIN, encoding="utf-8").read().splitlines()
i = next(k for k, l in enumerate(lines) if l.strip() == r"\begin{abstract}")
print("旧摘要词数（正确口径）:", count_words(lines[i + 1]))
lines[i + 1] = NEW_ABS
open(MAIN, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
print("新摘要词数（正确口径）:", count_words(NEW_ABS))

# 同步提交清单里的摘要块
def plain(s):
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\emph\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\code\{([^{}]*)\}", r"\1", s)
    s = s.replace("\\%", "%").replace("``", '"').replace("''", '"')
    s = s.replace("---", " - ").replace("--", "-")
    s = s.replace("$\\pm$", "+/-").replace("{,}", ",")
    s = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}$\\]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

txt = open(OUT, encoding="utf-8").read()
txt = re.sub(r"(?s)(\*\*Abstract\*\*（纯文本，直接粘贴）\n```\n).*?(\n```)", lambda m: m.group(1) + plain(NEW_ABS) + m.group(2), txt, count=1)
open(OUT, "w", encoding="utf-8", newline="").write(txt)
print("提交清单摘要块已同步")
