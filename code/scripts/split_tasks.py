# -*- coding: utf-8 -*-
"""S3 · 把 tier1/2 候选按模块切成 sub-agent 输入文件

输出目录: 实验记录/S3_parts/_inputs/
  taskA.json  config-core   （vllm/config/vllm.py, compilation.py）
  taskB.json  config-space  （vllm/config/ 其余）
  taskC.json  engine        （vllm/engine/, vllm/v1/engine/）
  taskD.json  runtime       （vllm/v1/core/, vllm/platforms/, vllm/v1/worker/）
  taskE.json  misc          （其余 tier<=2）
用法: python split_tasks.py
"""
import json
import os
from collections import Counter

SRC = r"F:\文献\AgentOps\实验记录\约束候选-配置相关.json"
OUT = r"F:\文献\AgentOps\实验记录\S3_parts\_inputs"


def classify(f):
    if f in ("vllm/config/vllm.py", "vllm/config/compilation.py"):
        return "taskA"
    if f in ("vllm/config/speculative.py", "vllm/config/parallel.py", "vllm/config/model.py"):
        return "taskB1"
    if f.startswith("vllm/config/"):
        return "taskB2"
    if f.startswith("vllm/engine/") or f.startswith("vllm/v1/engine/"):
        return "taskC"
    if f.startswith("vllm/v1/core/") or f.startswith("vllm/platforms/") or f.startswith("vllm/v1/worker/"):
        return "taskD"
    return "taskE"


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    groups = {k: [] for k in ("taskA", "taskB1", "taskB2", "taskC", "taskD", "taskE")}
    for c in data["candidates"]:
        if c["tier"] > 2:
            continue
        groups[classify(c["file"])].append(c)

    os.makedirs(OUT, exist_ok=True)
    summary = {}
    for k, arr in groups.items():
        files = Counter(c["file"] for c in arr)
        payload = {
            "task": k,
            "meta": data["meta"],
            "instructions": "见 F:/文献/AgentOps/实验记录/S3-agent-prompt模板.md（逐条读源码→结构化约束→写 S3_parts/{task}.json）",
            "counts": {"candidates": len(arr), "files": dict(files.most_common())},
            "candidates": arr,
        }
        p = os.path.join(OUT, f"{k}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        summary[k] = {"candidates": len(arr), "files": len(files)}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
