# -*- coding: utf-8 -*-
"""分析 S4 records.jsonl：状态统计 + 分组清单（供下一轮解锁）"""
import json
import sys
from collections import Counter, defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REC = r"F:\文献\AgentOps\实验记录\S4验证\records.jsonl"

records = []
with open(REC, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

# 去重（同 id 取最后一条）
by_id = {}
for r in records:
    by_id[r["constraint_id"]] = r
records = list(by_id.values())

print(f"总记录（去重后）: {len(records)}")
print("状态分布:", dict(Counter(r["status"] for r in records)))

print("\n=== confirmed（违反→构造期真报错）===")
for r in sorted(records, key=lambda x: x["constraint_id"]):
    if r["status"] == "confirmed":
        print(f'  {r["constraint_id"]} [{r.get("strategy","")}] {r["expr"][:80]}')
        print(f'      → {str(r.get("observed"))[:130]}')

print("\n=== no_error（基线可构造，但违反未在构造期报错）===")
for r in sorted(records, key=lambda x: x["constraint_id"]):
    if r["status"] == "no_error":
        print(f'  {r["constraint_id"]} [{r.get("strategy","")}] {r["expr"][:100]}')

print("\n=== blocked 分组（按策略/原因）===")
groups = defaultdict(list)
for r in sorted(records, key=lambda x: x["constraint_id"]):
    if r["status"] == "blocked":
        reason = (r.get("detail") or "")[:90]
        key = r.get("strategy") or "无候选类"
        key = key.split(":")[-1] if ":" in key else key
        groups[f"{key} | {reason[:60]}"].append(r["constraint_id"])
for k, ids in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f"  ({len(ids):3d}) {k}")
    print(f"        {', '.join(ids[:14])}{' ...' if len(ids) > 14 else ''}")