# -*- coding: utf-8 -*-
"""G1 审计辅助：把抽检样本的证据行连同源码上下文（±3 行）打出来，供逐条人工核对。

用法: python g1_audit_dump.py [样本.json] [vllm源码根] > 输出到控制台
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SAMPLE = r"F:\文献\AgentOps\实验记录\G1-抽检样本-第一批.json"
SRC = r"F:\文献\AgentOps\代码\third_party\vllm-v0.30.0"
CTX = 3

with open(sys.argv[1] if len(sys.argv) > 1 else SAMPLE, encoding="utf-8") as f:
    sample = json.load(f)
src_root = sys.argv[2] if len(sys.argv) > 2 else SRC
out_path = sys.argv[3] if len(sys.argv) > 3 else None

if out_path:
    sys.stdout = open(out_path, "w", encoding="utf-8")

cache = {}
def lines_of(rel):
    if rel not in cache:
        try:
            with open(os.path.join(src_root, rel), encoding="utf-8") as fh:
                cache[rel] = fh.read().splitlines()
        except Exception:
            cache[rel] = None
    return cache[rel]

for i, c in enumerate(sample["sampled"], 1):
    print("=" * 100)
    print(f'[{i}/20] {c["id"]}  ({c.get("type")})  scope={c.get("scope")}')
    print(f'expr: {c.get("expr")}')
    for e in c.get("evidence") or []:
        rel, line = e["file"], e["line"]
        arr = lines_of(rel)
        print(f'  --- {rel}:{line}  snippet={e.get("snippet")!r}')
        if arr is None:
            print("      !! 文件读取失败")
            continue
        lo, hi = max(1, line - CTX), min(len(arr), line + CTX)
        for n in range(lo, hi + 1):
            mark = ">>" if n == line else "  "
            print(f'   {mark}{n:5d}| {arr[n - 1]}')
    print()