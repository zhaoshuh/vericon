# -*- coding: utf-8 -*-
"""S3 · 跨模型抽取一致性对比（v1=deepseek-v4.1-flash 批次 vs v2=glm-5.3-flash 批次）

两个匹配口径：
  M1（严格·证据锚定）：两条约束的证据集存在相同 (file, line) → 视为同一约束
  M2（宽松·语义近似）：(params 集合, type) 相同 → 视为同一约束
输出：实验记录/S3-跨模型对比.json + 实验记录/S3-跨模型对比.md
用法: python compare_model_graphs.py [graph_v1] [graph_v2]
"""
import json
import sys
from collections import Counter, defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

G1 = r"F:\文献\AgentOps\实验记录\约束图.json"
G2 = r"F:\文献\AgentOps\实验记录\约束图-model2.json"
OUT_JSON = r"F:\文献\AgentOps\实验记录\S3-跨模型对比.json"
OUT_MD = r"F:\文献\AgentOps\实验记录\S3-跨模型对比.md"


def load(path):
    g = json.load(open(path, encoding="utf-8"))
    return g


def evidence_keys(node):
    return {(e.get("file"), e.get("line")) for e in (node.get("evidence") or []) if e.get("file") and e.get("line")}


def semantic_key(node):
    return (tuple(sorted(node.get("params") or [])), node.get("type"))


def main():
    p1 = sys.argv[1] if len(sys.argv) > 1 else G1
    p2 = sys.argv[2] if len(sys.argv) > 2 else G2
    g1, g2 = load(p1), load(p2)
    n1, n2 = g1["nodes"], g2["nodes"]

    # 索引
    ev1 = defaultdict(set)   # (file,line) -> v1 ids
    sem1 = defaultdict(set)  # semantic key -> v1 ids
    for n in n1:
        for k in evidence_keys(n):
            ev1[k].add(n["id"])
        sem1[semantic_key(n)].add(n["id"])
    ev2 = defaultdict(set)
    sem2 = defaultdict(set)
    for n in n2:
        for k in evidence_keys(n):
            ev2[k].add(n["id"])
        sem2[semantic_key(n)].add(n["id"])

    def matched(n, ev_index, sem_index):
        m1 = any(k in ev_index for k in evidence_keys(n))
        m2 = semantic_key(n) in sem_index
        return m1, m2

    v2_m1, v2_m2, v2_none = 0, 0, []
    for n in n2:
        m1, m2 = matched(n, ev1, sem1)
        v2_m1 += m1
        v2_m2 += m2
        if not m1 and not m2:
            v2_none.append(n["id"])

    v1_m1, v1_m2, v1_none = 0, 0, []
    for n in n1:
        m1, m2 = matched(n, ev2, sem2)
        v1_m1 += m1
        v1_m2 += m2
        if not m1 and not m2:
            v1_none.append(n["id"])

    # per-scope
    scope_stats = {}
    for scope in sorted({n.get("scope") for n in n2}):
        ids = [n["id"] for n in n2 if n.get("scope") == scope]
        hit = 0
        for cid in ids:
            node = next(x for x in n2 if x["id"] == cid)
            m1, m2 = matched(node, ev1, sem1)
            hit += (m1 or m2)
        scope_stats[scope] = {"v2": len(ids), "matched_by_v1": hit}

    doc = {
        "v1": {"model": "deepseek-v4.1-flash (harness default)", "total": len(n1), "path": p1},
        "v2": {"model": "glm-5.3-flash (pinned)", "total": len(n2), "path": p2},
        "match_definitions": {
            "M1": "证据锚定：存在相同 (file,line)",
            "M2": "语义近似：(params, type) 相同",
        },
        "v2_matched_by_v1": {"M1": v2_m1, "M2": v2_m2, "union": v2_m1 + v2_m2 - sum(
            1 for n in n2 if matched(n, ev1, sem1)[0] and matched(n, ev1, sem1)[1]), "none": len(v2_none)},
        "v1_matched_by_v2": {"M1": v1_m1, "M2": v1_m2, "none": len(v1_none)},
        "v2_only_ids": v2_none,
        "v1_only_ids": v1_none,
        "per_scope_v2": scope_stats,
    }
    json.dump(doc, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    md = [
        "# S3 · 跨模型抽取一致性（v1 vs v2）",
        "",
        f"> v1 = {doc['v1']['model']}（{len(n1)} 条）｜ v2 = {doc['v2']['model']}（{len(n2)} 条）",
        "> 匹配口径：M1 = 证据锚定（相同 file:line）；M2 = 语义近似（params+type）",
        "",
        "| 方向 | M1 命中 | M2 命中 | 未命中 |",
        "|---|---|---|---|",
        f"| v2 被 v1 覆盖 | {v2_m1}/{len(n2)} | {v2_m2}/{len(n2)} | {len(v2_none)} |",
        f"| v1 被 v2 覆盖 | {v1_m1}/{len(n1)} | {v1_m2}/{len(n1)} | {len(v1_none)} |",
        "",
        "## 结论口径",
        "",
        f"- **v2（GLM）相对 v1 的召回**：证据锚定 {v2_m1/len(n2):.1%}，语义近似 {v2_m2/len(n2):.1%}",
        f"- **v1（DeepSeek）相对 v2 的召回**：证据锚定 {v1_m1/len(n1):.1%}，语义近似 {v1_m2/len(n1):.1%}",
        "- 未命中条目（v2_only / v1_only）见 JSON；两者取并集可作为『跨模型增强约束集』候选，",
        "  经 S4 证伪后可扩充 artifact（论文的跨模型鲁棒性小节）。",
        "",
    ]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))
    print(json.dumps({"v2_total": len(n2), "v2_matched_M1": v2_m1, "v2_matched_M2": v2_m2,
                      "v2_only": len(v2_none), "v1_total": len(n1),
                      "v1_matched_M1": v1_m1, "v1_only": len(v1_none)}, ensure_ascii=False))
    print("->", OUT_JSON)
    print("->", OUT_MD)


if __name__ == "__main__":
    main()
