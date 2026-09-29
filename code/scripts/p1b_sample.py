# -*- coding: utf-8 -*-
"""P1b · 金标准评测：从 3,129 条参数相关候选中分层抽样 150 条（tier1/2/3 各 50），
输出样本 JSON + 源码上下文转储（供逐条标注：真约束 / 非约束 / 不确定）。

用法: python p1b_sample.py
输出: 实验记录/P1b-金标准样本.json
      C:\...\Temp\opencode\p1b_dump.txt（源码上下文）
"""
import json
import os
import random
import sys

SRC = r"F:\文献\AgentOps\实验记录\约束候选-配置相关.json"
OUT = r"F:\文献\AgentOps\实验记录\P1b-金标准样本.json"
DUMP = r"C:\Users\Administrator\AppData\Local\Temp\opencode\p1b_dump.txt"
SRC_ROOT = r"F:\文献\AgentOps\代码\third_party\vllm-v0.30.0"
SEED = 20260927
N_PER_TIER = 50
CTX = 3


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    by_tier = {1: [], 2: [], 3: []}
    for c in data["candidates"]:
        by_tier[c["tier"]].append(c)

    rng = random.Random(SEED)
    sample = []
    for t in (1, 2, 3):
        pool = by_tier[t]
        sample += rng.sample(pool, min(N_PER_TIER, len(pool)))

    json.dump({"seed": SEED, "n": len(sample), "sites": sample},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    lines_cache = {}

    def lines_of(rel):
        if rel not in lines_cache:
            try:
                lines_cache[rel] = open(os.path.join(SRC_ROOT, rel), encoding="utf-8").read().splitlines()
            except Exception:
                lines_cache[rel] = None
        return lines_cache[rel]

    with open(DUMP, "w", encoding="utf-8") as out:
        for i, c in enumerate(sample, 1):
            out.write("=" * 96 + "\n")
            out.write(f'[{i}/150] {c["file"]}:{c["line"]}  ({c["kind"]}, tier={c["tier"]})\n')
            out.write(f'  matched_params: {c.get("matched_params")}\n')
            out.write(f'  condition: {(c.get("condition") or "")[:220]}\n')
            if c.get("message"):
                out.write(f'  message: {c["message"][:180]}\n')
            arr = lines_of(c["file"])
            if arr is None:
                out.write("  !! source unreadable\n")
                continue
            lo, hi = max(1, c["line"] - CTX), min(len(arr), c["line"] + CTX)
            for n in range(lo, hi + 1):
                mark = ">>" if n == c["line"] else "  "
                out.write(f'   {mark}{n:5d}| {arr[n-1]}\n')
            out.write("\n")

    print(f"sample={len(sample)} -> {OUT}")
    print(f"dump -> {DUMP}")


if __name__ == "__main__":
    main()
