# -*- coding: utf-8 -*-
"""从三批原始标注重建 c1_results.csv（修复被测试脚本覆盖的问题）"""
import csv
import os

C1 = "/mnt/f/文献/AgentOps/实验记录/C1-人类盲标"
rows = []
for i in (1, 2, 3):
    p = f"{C1}/c1_part{i}.csv"
    with open(p, encoding="utf-8-sig") as fh:
        part = list(csv.DictReader(fh))
    print(f"part{i}: {len(part)} 行")
    rows += part
assert len(rows) == 150

with open(f"{C1}/c1_results.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "verdict", "note", "file", "line", "tier"])
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in ["id", "verdict", "note", "file", "line", "tier"]})
print("重建 c1_results.csv:", len(rows), "行")
from collections import Counter
print("verdict 分布:", Counter(r["verdict"].strip().upper()[:1] for r in rows))
