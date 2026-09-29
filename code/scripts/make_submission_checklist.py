# -*- coding: utf-8 -*-
"""① 对齐 cover letter 3 处措辞 ② 生成 ScholarOne 提交清单（含纯文本摘要/关键词）"""
import re

AP = "/mnt/f/文献/AgentOps"
COVER = f"{AP}/论文/latex/cover-letter.txt"
MAIN = f"{AP}/论文/latex/main.tex"
OUT = f"{AP}/论文/latex/投稿-提交清单.md"

pairs = [
    ("that it decays: of SCOOT's three published rules, two no longer hold in current releases (one runtime guard was removed upstream; one conditional rule lost practical force as defaults changed), and six of six tested folk rules are unenforced on a second engine.",
     "that it decays: of SCOOT's three published rules, two have lost their force in current releases (one runtime guard was removed upstream; one keeps its semantics but is rendered dormant by changed defaults), and six of six tested folk rules are unenforced on a second engine."),
    ("we show that two of its three published rules no longer hold in current releases (a removed runtime guard and default-driven decay; measured across five releases and three execution-tested versions)",
     "we show that two of its three published rules have lost their force in current releases (a removed runtime guard and default-driven dormancy; measured across five releases and three execution-tested versions)"),
    ("with a formal constraint algebra, two properties (reliability and zero-violation), and an analytical cost relation",
     "with a formal constraint algebra, two bounded properties (witness-level confirmation and zero-violation sampling), and an analytical cost relation"),
]
t = open(COVER, encoding="utf-8").read()
for i, (o, n) in enumerate(pairs, 1):
    c = t.count(o)
    print(f"cover pair{i}: count={c}")
    if c == 1:
        t = t.replace(o, n)
open(COVER, "w", encoding="utf-8", newline="").write(t)

# ---- 纯文本摘要 ----
tex = open(MAIN, encoding="utf-8").read()
lines = tex.splitlines()
abs_idx = next(i for i, l in enumerate(lines) if l.strip() == r"\begin{abstract}")
abstract = lines[abs_idx + 1]
kw_idx = next(i for i, l in enumerate(lines) if l.strip() == r"\begin{IEEEkeywords}")
keywords = lines[kw_idx + 1]

def plain(s):
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\emph\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\code\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\%", "%", s)
    s = re.sub(r"\\code\{file:line\}", "file:line", s)
    s = s.replace("``", '"').replace("''", '"')
    s = s.replace("---", " - ").replace("--", "-")
    s = s.replace("$\\pm$", "+/-").replace("$\\neq$", "!=").replace("$\\approx$", "~")
    s = s.replace("\\,", " ").replace("{,}", ",").replace("~", " ")
    s = re.sub(r"\\[a-zA-Z]+(\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}$\\]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

abstract_txt = plain(abstract)
kw_txt = plain(keywords)
print("摘要纯文本词数:", len(abstract_txt.split()))
print("关键词:", kw_txt)

checklist = f"""# TSE · ScholarOne 投稿提交清单（2026-09-29 就绪）

> 说明：**最后一步（登录 + 勾选作者声明 + 点 Submit）只能由作者本人完成**——涉及账号与法律性承诺，不可代签。
> 本清单把其余事项全部准备好；照做约 10–15 分钟。

## 0) 发射前预检（已通过）
- 稿件：`F:\\文献\\AgentOps\\论文\\latex\\main.pdf` — **11 页、US Letter、34 个字体全部嵌入、0 超链接、406 KB**
- `main.tex` 编译：**0 Overfull、0 未定义引用**；摘要 **238/250 词**
- 原始性自检：全文未投稿/未发表；单作者；无利益冲突（封面信已声明）

## 1) 提交入口与账号
1. 打开 IEEE TSE 的 ScholarOne：`https://mc.manuscriptcentral.com/tse`（以 TSE 作者指南页面的最新链接为准）
2. 登录（若首次需注册；建议先补 ORCID）

## 2) 逐项填写（可直接复制）

**Article Type**：Regular Paper

**Title**
```
VeriCon: Mining, Falsifying, and Injecting Configuration Constraints for LLM Inference Engines
```

**Abstract**（纯文本，直接粘贴）
```
{abstract_txt}
```

**Index Terms / Keywords**
```
{kw_txt}
```

**Authors**：Shuheng Zhao ｜ Independent Researcher ｜ zshbdfdc@163.com ｜ 单作者（无共同作者）

**Cover Letter**：上传 `F:\\文献\\AgentOps\\论文\\latex\\cover-letter.txt`（内容含防御性定位段 + 建议审稿人）

**Manuscript**：上传 `F:\\文献\\AgentOps\\论文\\latex\\main.pdf`

**Suggested Reviewers**（6 人；**邮箱需你查证后填**，ScholarOne 一般要求姓名+单位+邮箱）
1. Christian Kaestner — Carnegie Mellon University（配置分析；ICSE'14 约束挖掘）
2. Sarah Nadi — University of Alberta（配置约束；ICSE'14 第一作者）
3. Tianyin Xu — University of Illinois Urbana-Champaign（LLM 配置校验；Ciri）
4. Pengfei Chen — Sun Yat-sen University（LLM-for-systems；LLMConf/InferLog）
5. Jianguo Wang — Purdue University（LLM 数据库调优；GPTuner）
6. Zhi Wang — Tsinghua University（LLM 推理引擎调优；SCOOT）

**Opposed Reviewers**：无

## 3) 需要你本人确认的三件事（我不能代做）

- [ ] **评审模式**：在 TSE 作者指南确认当前是**单盲**还是**双盲**。若为双盲，需要一份**匿名版 PDF**（去掉作者名/邮箱/footnote）——告诉我，我 5 分钟生成。
- [ ] **AI 使用披露**：若表单有 "generative AI used" 项，如实勾选并简述：*"LLM agents were used as part of the method (extraction and labeling passes), as described in the paper; all evidence is source-anchored and execution-verified."*
- [ ] **数据/代码可用性声明**：如要求填 URL 且仓库未上线，可填 *"Artifacts (constraint graphs with evidence, harnesses, raw records, scripts) are prepared for release with the paper; repository URL to be provided at acceptance."*

## 4) 勾选与提交（作者声明）
原创性声明 ｜ 全体作者同意 ｜ 未同时投他刊 ｜ 无利益冲突 ｜ 遵守 IEEE 出版伦理与 AI 政策 → **Submit**

## 5) 提交后
把确认邮件（Manuscript ID）发我，我登记进 `F:\\文献\\AgentOps\\01-进度.md`；之后若进入返修，C 批（GPU/V1 端到端锚点）可那时再补。
"""
open(OUT, "w", encoding="utf-8", newline="").write(checklist)
print("清单已写:", OUT)
PYEOF_MARK = None
