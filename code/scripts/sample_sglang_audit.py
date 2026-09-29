# -*- coding: utf-8 -*-
"""P3 SGLang 抽检样本：从 约束图-sglang.json 按类型分层抽 40 条（seed 2026）
输出：实验记录/P3-sglang抽检样本.json（含 "sampled" 键，供 g1_audit_dump.py 使用）
"""
import json
import random

GRAPH = r"F:\文献\AgentOps\实验记录\约束图-sglang.json"
OUT = r"F:\文献\AgentOps\实验记录\P3-sglang抽检样本.json"
SEED = 2026

QUOTA = {
    "implication": 13,
    "mutual_exclusion": 6,
    "enum": 5,
    "arithmetic": 5,
    "range": 4,
    "inequality": 4,
    "type": 3,
}


def main():
    g = json.load(open(GRAPH, encoding="utf-8"))
    nodes = g["nodes"]
    by_type = {}
    for n in nodes:
        by_type.setdefault(n.get("type"), []).append(n)

    rng = random.Random(SEED)
    sampled = []
    for t, k in QUOTA.items():
        pool = by_type.get(t, [])
        sampled += rng.sample(pool, min(k, len(pool)))
    # 不足 40 时从剩余里补
    if len(sampled) < 40:
        have = {id(x) for x in sampled}
        rest = [n for n in nodes if id(n) not in have]
        sampled += rng.sample(rest, min(40 - len(sampled), len(rest)))

    json.dump({"seed": SEED, "n": len(sampled), "sampled": sampled},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    from collections import Counter
    print("sampled:", len(sampled), dict(Counter(n.get("type") for n in sampled)))
    print("->", OUT)


if __name__ == "__main__":
    main()
