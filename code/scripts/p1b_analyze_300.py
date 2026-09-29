# -*- coding: utf-8 -*-
"""P1b 第二批标注结果 + 合并（300 站点）召回分析

第一批：P1b-金标准样本.json / P1b-标注结果.json（150：C=96, N=54）
第二批：P1b-金标准样本2.json（150：C=107, N=43）
图：约束图-v1-ext.json（716）
输出：实验记录/P1b-标注结果2.json、P1b-金标准-结果-300.md、P1b-300汇总.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REC = r"F:\文献\AgentOps\实验记录"
GRAPH = os.path.join(REC, "约束图-v1-ext.json")

# 第二批人工判定为 N 的下标（1-based；其余为 C）
N2 = (
    [11, 19, 26, 32, 39]
    + [53, 57, 67, 74, 76, 78, 81, 84, 85, 88, 89, 93, 99]
    + [101, 103, 105, 106, 109, 111, 112, 113, 114, 115, 116, 119, 121, 123,
       125, 128, 129, 130, 131, 134, 136, 140, 148, 149, 150]
)


def load_sample(path):
    return json.load(open(path, encoding="utf-8"))["sites"]


def evidence_index(graph):
    ev = {}
    for n in graph["nodes"]:
        for e in n.get("evidence") or []:
            ev.setdefault((e.get("file"), e.get("line")), []).append(n["id"])
    return ev


def analyze(sample, n_idx, ev, tag):
    rows = []
    for i, s in enumerate(sample, 1):
        label = "N" if i in n_idx else "C"
        key = (s["file"], s["line"])
        hit = ev.get(key, [])
        hit_pm1 = hit or ev.get((s["file"], s["line"] + 1), []) or ev.get((s["file"], s["line"] - 1), [])
        rows.append({"idx": i, "file": s["file"], "line": s["line"], "tier": s["tier"],
                     "label": label, "captured_exact": bool(hit), "captured_pm1": bool(hit_pm1)})
    C = [r for r in rows if r["label"] == "C"]
    N = [r for r in rows if r["label"] == "N"]
    stats = {
        "tag": tag, "n": len(rows), "C": len(C), "N": len(N),
        "recall_exact": round(sum(r["captured_exact"] for r in C) / len(C), 4),
        "recall_pm1": round(sum(r["captured_pm1"] for r in C) / len(C), 4),
        "N_hit": sum(1 for r in N if r["captured_pm1"]),
        "by_tier": {},
    }
    for t in (1, 2, 3):
        sub = [r for r in C if r["tier"] == t]
        if sub:
            stats["by_tier"][t] = {
                "C": len(sub),
                "exact": sum(r["captured_exact"] for r in sub),
                "pm1": sum(r["captured_pm1"] for r in sub),
            }
    return rows, stats


def main():
    graph = json.load(open(GRAPH, encoding="utf-8"))
    ev = evidence_index(graph)

    s1 = load_sample(os.path.join(REC, "P1b-金标准样本.json"))
    lab1 = json.load(open(os.path.join(REC, "P1b-标注结果.json"), encoding="utf-8"))
    n1 = set(lab1["labels"]["N_indices"])
    rows1, stats1 = analyze(s1, n1, ev, "第一批(150)")

    s2 = load_sample(os.path.join(REC, "P1b-金标准样本2.json"))
    rows2, stats2 = analyze(s2, set(N2), ev, "第二批(150)")
    json.dump({"labels": {"N_indices": sorted(N2), "default": "C"}, "rows": rows2, "stats": stats2},
              open(os.path.join(REC, "P1b-标注结果2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # 合并 300
    C_all = [r for r in rows1 + rows2 if r["label"] == "C"]
    N_all = [r for r in rows1 + rows2 if r["label"] == "N"]
    comb = {
        "n": 300, "C": len(C_all), "N": len(N_all),
        "recall_exact": round(sum(r["captured_exact"] for r in C_all) / len(C_all), 4),
        "recall_pm1": round(sum(r["captured_pm1"] for r in C_all) / len(C_all), 4),
        "N_hit": sum(1 for r in N_all if r["captured_pm1"]),
        "by_tier": {},
    }
    for t in (1, 2, 3):
        sub = [r for r in C_all if r["tier"] == t]
        comb["by_tier"][t] = {
            "C": len(sub),
            "exact": sum(r["captured_exact"] for r in sub),
            "pm1": sum(r["captured_pm1"] for r in sub),
        }
    json.dump({"batch1": stats1, "batch2": stats2, "combined": comb},
              open(os.path.join(REC, "P1b-300汇总.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    md = [
        "# P1b · 金标准召回（扩样 300 站点）",
        "",
        "> 抽样：3,129 条参数相关候选中分层随机（tier 各 50/批，两批独立 seed）；",
        "> 标注：评估者逐条对照源码；第二批另做独立盲标一致性检验；",
        "> 抓取口径：约束图（`约束图-v1-ext.json`，716 条）存在证据行 = 捕获。",
        "",
        "## 合并结果（300 站点）",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        f"| 真约束（C） | {comb['C']} |",
        f"| **召回（精确行）** | **{comb['recall_exact']:.1%}** |",
        f"| **召回（±1 行）** | **{comb['recall_pm1']:.1%}** |",
        f"| 非约束站点带图证据（误报代理） | {comb['N_hit']}/{comb['N']} |",
        "",
        "## 分层（合并）",
        "",
        "| tier | C | 召回（精确） | 召回（±1） |",
        "|---|---|---|---|",
    ]
    for t in (1, 2, 3):
        v = comb["by_tier"][t]
        md.append(f"| {t} | {v['C']} | {v['exact']}/{v['C']} = {v['exact']/v['C']:.0%} | {v['pm1']}/{v['C']} = {v['pm1']/v['C']:.0%} |")
    md += [
        "",
        "## 两批对照",
        "",
        "| 批次 | n | C | 召回（精确） | 召回（±1） |",
        "|---|---|---|---|---|",
        f"| 第一批 | {stats1['n']} | {stats1['C']} | {stats1['recall_exact']:.1%} | {stats1['recall_pm1']:.1%} |",
        f"| 第二批 | {stats2['n']} | {stats2['C']} | {stats2['recall_exact']:.1%} | {stats2['recall_pm1']:.1%} |",
        f"| **合并** | **300** | **{comb['C']}** | **{comb['recall_exact']:.1%}** | **{comb['recall_pm1']:.1%}** |",
        "",
        "*生成：2026-09-28 ｜ 数据：P1b-标注结果.json / P1b-标注结果2.json*",
    ]
    open(os.path.join(REC, "P1b-金标准-结果-300.md"), "w", encoding="utf-8").write("\n".join(md))

    print(json.dumps({"batch1": {k: stats1[k] for k in ("C", "recall_exact", "recall_pm1")},
                      "batch2": {k: stats2[k] for k in ("C", "recall_exact", "recall_pm1")},
                      "combined": {k: comb[k] for k in ("C", "recall_exact", "recall_pm1", "N_hit")},
                      "by_tier": comb["by_tier"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
