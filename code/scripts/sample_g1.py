# -*- coding: utf-8 -*-
"""G1 · 从约束图可复现抽样（固定种子）

用法: python sample_g1.py [约束图.json] [--n 20] [--seed 42]
输出: 实验记录/G1-抽检样本-第一批.json + 控制台 markdown 表格行
"""
import json
import random
import sys
import os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_GRAPH = r"F:\文献\AgentOps\实验记录\约束图.json"
DEFAULT_OUT = r"F:\文献\AgentOps\实验记录\G1-抽检样本-第一批.json"


def main():
    args = sys.argv[1:]
    graph_path = DEFAULT_GRAPH
    n, seed = 20, 42
    out_path = DEFAULT_OUT
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--n":
            n = int(args[i + 1]); i += 2
        elif a == "--seed":
            seed = int(args[i + 1]); i += 2
        elif a.endswith(".json") and os.path.exists(a):
            graph_path = a; i += 1
        else:
            out_path = a; i += 1

    with open(graph_path, encoding="utf-8") as f:
        graph = json.load(f)
    nodes = graph["nodes"]
    rng = random.Random(seed)
    sampled = rng.sample(nodes, min(n, len(nodes)))

    payload = {
        "seed": seed,
        "n": len(sampled),
        "graph_total": len(nodes),
        "graph_version": graph.get("meta", {}),
        "sampled": [{"id": c.get("id"), "expr": c.get("expr"), "type": c.get("type"),
                     "scope": c.get("scope"), "evidence": c.get("evidence")} for c in sampled],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"seed={seed} sampled={len(sampled)}/{len(nodes)} -> {out_path}")
    print("\n| # | 约束 ID | expr | 证据（file:line） |")
    print("|---|---|---|---|")
    for idx, c in enumerate(sampled, 1):
        ev = c.get("evidence") or [{}]
        evs = "; ".join(f'{e.get("file","?")}:{e.get("line","?")}' for e in ev)
        print(f'| {idx} | {c.get("id")} | `{c.get("expr")}` | {evs} |')


if __name__ == "__main__":
    main()
