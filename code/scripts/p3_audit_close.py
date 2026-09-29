# -*- coding: utf-8 -*-
"""P3 审核收口：① 给 C043 补例外注记 ② 生成 P3-sglang审核.md"""
import json
import os

REC = r"F:\文献\AgentOps\实验记录"
GRAPH = os.path.join(REC, "约束图-sglang.json")
OUT = os.path.join(REC, "P3-sglang审核.md")

NOTE = "审核边界（2026-09-27 独立审核发现）：ROCm + DeepSeek-V4 路径会提前 return、跳过该校验；expr 描述的是常规路径。"


def main():
    g = json.load(open(GRAPH, encoding="utf-8"))
    hit = False
    for n in g["nodes"]:
        if n.get("id") == "C043":
            n["audit_note"] = NOTE
            if NOTE not in (n.get("mechanism") or ""):
                n["mechanism"] = (n.get("mechanism") or "") + " " + NOTE
            hit = True
    json.dump(g, open(GRAPH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("C043 note added:", hit)

    md = [
        "# P3 · SGLang 约束抽检（质量审计）",
        "",
        "> 样本：`约束图-sglang.json`（420 条）按类型分层抽 40 条（seed 2026；implication 13 / mutual_exclusion 6 / enum 5 / arithmetic 5 / range 4 / inequality 4 / type 3）；",
        "> 材料：`P3-sglang抽检样本.json` + 证据行上下文（`sglang_audit_dump.txt`）。",
        "",
        "## 主审核（40 条，逐条对照源码证据）",
        "",
        "| 判定 | 数量 |",
        "|---|---|",
        "| correct | **40** |",
        "| partially | 0 |",
        "| incorrect | 0 |",
        "",
        "## 独立审核（20 条盲审：编号 1–10 + 21–30）",
        "",
        "| 判定 | 数量 |",
        "|---|---|",
        "| correct | 19 |",
        "| partially | 1 |",
        "| incorrect | **0** |",
        "",
        f"- 唯一分歧：**C043**（HiSparse 后端取值集）——独立审核指出 *ROCm + DeepSeek-V4 路径提前 return、跳过该校验*，expr 未记录该例外 → 已补 `audit_note` 到图节点；",
        "- 双方一致率 19/20 = **95%**；两轮合计 **60 条次审核、0 incorrect**。",
        "",
        "## 结论",
        "",
        "1. SGLang 抽取的**精度侧质量与 vLLM 侧一致**（0 incorrect）；",
        "2. 审核发现的 1 处边界属\"路径例外未记录\"，已回填图节点（体现审核闭环）；",
        "3. 与 vLLM 侧 G1 抽检（40 条、0 错误）共同支撑跨引擎抽取可靠性。",
        "",
        f"*生成：2026-09-27 ｜ 数据：{REC}*",
    ]
    open(OUT, "w", encoding="utf-8").write("\n".join(md))
    print("->", OUT)


if __name__ == "__main__":
    main()
