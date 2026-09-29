# -*- coding: utf-8 -*-
"""从 runs.jsonl 重建 runs.csv（修复并发丢行 + 字段超限问题）"""
import csv
import json
import os
import sys

sys.path.insert(0, r"F:\文献\AgentOps\代码")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10 ** 9)
from agentops.record import flatten  # noqa: E402

SRC = r"F:\文献\AgentOps\实验记录\runs.jsonl"
DST = r"F:\文献\AgentOps\实验记录\runs.csv"

rows = []
fieldnames = []
bad = 0
for line in open(SRC, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        bad += 1
        continue
    f = flatten(d)
    rows.append(f)
    for k in f:
        if k not in fieldnames:
            fieldnames.append(k)

tmp = DST + ".tmp"
with open(tmp, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fieldnames})
os.replace(tmp, DST)
print(f"rebuilt: rows={len(rows)} cols={len(fieldnames)} bad_lines={bad}")
