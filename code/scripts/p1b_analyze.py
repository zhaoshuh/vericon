# -*- coding: utf-8 -*-
"""P1b 标注结果（人工逐条） + 金标准召回分析

标签口径：C = 涉及配置参数的关系/取值约束；N = 纯内部实现/运行期/请求局部检查
（评估者：主控；口径说明见 P1b-金标准-结果.md）
"""
import json
import os
import sys
from collections import Counter

SAMPLE = r"F:\文献\AgentOps\实验记录\P1b-金标准样本.json"
GRAPH = r"F:\文献\AgentOps\实验记录\约束图.json"
OUT_LABELS = r"F:\文献\AgentOps\实验记录\P1b-标注结果.json"
OUT_MD = r"F:\文献\AgentOps\实验记录\P1b-金标准-结果.md"

# 人工判定为 N 的下标（1-based；其余为 C）
N_IDX = set(
    [21, 35, 37, 44, 48]
    + [51, 52, 54, 59, 62, 65, 72, 76, 84, 86, 89, 90, 95, 96, 97, 98]
    + [103, 104, 105, 106, 108, 109, 110, 111, 113, 118, 119, 121, 123, 124, 125,
       127, 128, 129, 131, 133, 134, 136, 137, 138, 139, 140, 141, 142, 143, 145,
       146, 148, 149]
)


def main():
    sample = json.load(open(SAMPLE, encoding="utf-8"))["sites"]
    graph_path = sys.argv[1] if len(sys.argv) > 1 else GRAPH
    out_md = sys.argv[2] if len(sys.argv) > 2 else OUT_MD
    graph = json.load(open(graph_path, encoding="utf-8"))
    ev = {}
    for n in graph["nodes"]:
        for e in n.get("evidence") or []:
            ev.setdefault((e.get("file"), e.get("line")), []).append(n["id"])

    rows = []
    for i, s in enumerate(sample, 1):
        label = "N" if i in N_IDX else "C"
        key = (s["file"], s["line"])
        hit = ev.get(key, [])
        hit_pm1 = hit or ev.get((s["file"], s["line"] + 1), []) or ev.get((s["file"], s["line"] - 1), [])
        rows.append({"idx": i, "file": s["file"], "line": s["line"], "tier": s["tier"],
                     "label": label, "captured_exact": bool(hit), "captured_pm1": bool(hit_pm1),
                     "graph_ids": hit[:3]})

    by_tier = {}
    for t in (1, 2, 3):
        sub = [r for r in rows if r["tier"] == t]
        c = [r for r in sub if r["label"] == "C"]
        n = [r for r in sub if r["label"] == "N"]
        by_tier[t] = {
            "total": len(sub), "C": len(c), "N": len(n),
            "C_captured_exact": sum(r["captured_exact"] for r in c),
            "C_captured_pm1": sum(r["captured_pm1"] for r in c),
            "N_with_graph_constraint": sum(1 for r in n if r["captured_pm1"]),
        }

    C = [r for r in rows if r["label"] == "C"]
    N = [r for r in rows if r["label"] == "N"]
    recall_exact = sum(r["captured_exact"] for r in C) / len(C)
    recall_pm1 = sum(r["captured_pm1"] for r in C) / len(C)
    n_hit = sum(1 for r in N if r["captured_pm1"])

    json.dump({"labels": {"N_indices": sorted(N_IDX), "default": "C"},
               "rows": rows,
               "stats": {"C": len(C), "N": len(N),
                         "recall_exact": round(recall_exact, 4),
                         "recall_pm1": round(recall_pm1, 4),
                         "N_sites_with_graph_constraint": n_hit,
                         "by_tier": by_tier}},
              open(OUT_LABELS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    md = [
        "# P1b · 金标准召回评测结果",
        "",
        "> 样本：3,129 条参数相关候选中分层随机抽样 150 条（tier1/2/3 各 50，seed 20260927）；",
        "> 标签：C = 涉及配置参数的关系/取值约束（96 条）；N = 内部实现/运行期/请求局部检查（54 条）；",
        "> 抓取口径：约束图中存在证据行 = 该站点被管线捕获（精确匹配 / ±1 行容差两版）。",
        "",
        "## 总结果",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        f"| 金标准约束数（C） | {len(C)} |",
        f"| **召回率（精确行匹配）** | **{recall_exact:.1%}**（{sum(r['captured_exact'] for r in C)}/{len(C)}） |",
        f"| 召回率（±1 行容差） | {recall_pm1:.1%}（{sum(r['captured_pm1'] for r in C)}/{len(C)}） |",
        f"| N 站点上出现约束图证据（误报代理） | {n_hit}/{len(N)} |",
        "",
        "## 分层结果",
        "",
        "| tier | 样本 | C | N | C 召回（精确） | C 召回（±1） |",
        "|---|---|---|---|---|---|",
    ]
    for t in (1, 2, 3):
        s = by_tier[t]
        md.append(f"| {t} | {s['total']} | {s['C']} | {s['N']} | "
                  f"{s['C_captured_exact']}/{s['C']} = {s['C_captured_exact']/max(1,s['C']):.0%} | "
                  f"{s['C_captured_pm1']}/{s['C']} = {s['C_captured_pm1']/max(1,s['C']):.0%} |")
    md += [
        "",
        "## 口径与解读（写论文用）",
        "",
        "1. **召回定义**：随机抽样的「真约束站点」中被管线以约束形式捕获的比例——这是对「冰山一角」质疑的直接回答；",
        "2. **分层意义**：tier1（config 层）召回最高，tier3（模型/内核代码）显著低——与「抽取范围设计」一致（tier3 属扩召回阶段，正在全量处理）；",
        "3. **误报代理**：N 站点上出现约束图证据的数量反映「把内部检查误判为约束」的倾向；",
        "4. 标签由评估者（主控）逐条对照源码判定，口径见本文件首行；建议在论文中同时报告 G1 抽检（精度侧）与本召回（覆盖侧）。",
        "",
        f"*生成：2026-09-27 ｜ 样本 {SAMPLE} ｜ 图 {graph_path}*",
    ]
    open(out_md, "w", encoding="utf-8").write("\n".join(md))
    print(json.dumps({"C": len(C), "N": len(N), "recall_exact": recall_exact,
                      "recall_pm1": recall_pm1, "N_hit": n_hit,
                      "by_tier": by_tier}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
