# -*- coding: utf-8 -*-
"""P1a · 把 tier3 候选（2,766 条）切成 10 个批次，供全量召回 Agent 处理

输入: 实验记录/约束候选-配置相关.json
输出: 实验记录/S3_parts_tier3/_inputs/batch01..10.json
用法: python split_tier3.py [n_batches]
"""
import json
import os
import sys
from collections import Counter

SRC = r"F:\文献\AgentOps\实验记录\约束候选-配置相关.json"
OUT = r"F:\文献\AgentOps\实验记录\S3_parts_tier3\_inputs"


def main():
    n_batches = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    data = json.load(open(SRC, encoding="utf-8"))
    tier3 = [c for c in data["candidates"] if c["tier"] == 3]
    tier3.sort(key=lambda c: (c["file"], c["line"]))
    os.makedirs(OUT, exist_ok=True)

    per = (len(tier3) + n_batches - 1) // n_batches
    total = 0
    for i in range(n_batches):
        chunk = tier3[i * per:(i + 1) * per]
        if not chunk:
            continue
        payload = {
            "task": f"tier3-batch{i+1:02d}",
            "meta": {
                "source": "约束候选-配置相关.json（tier=3）",
                "note": "tier3 = vllm/config 与 engine/core 之外的候选（模型/量化/运行期代码），噪声比例更高；"
                        "仅保留'配置参数之间/取值'的约束，内部实现检查一律 dropped",
            },
            "counts": {"candidates": len(chunk), "files": dict(Counter(c["file"] for c in chunk).most_common(40))},
            "candidates": chunk,
        }
        p = os.path.join(OUT, f"batch{i+1:02d}.json")
        json.dump(payload, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        total += len(chunk)
        print(f"batch{i+1:02d}: {len(chunk)} candidates -> {p}")
    print(f"total={total} batches={n_batches}")


if __name__ == "__main__":
    main()
