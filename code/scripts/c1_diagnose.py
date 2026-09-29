# -*- coding: utf-8 -*-
"""C1 诊断：第三遍盲标 vs 既有评测者标签的分歧结构"""
import csv
import json
from collections import Counter

C1 = "/mnt/f/文献/AgentOps/实验记录/C1-人类盲标"
records = json.load(open(f"{C1}/C1-导入结果.json", encoding="utf-8"))["records"]

ct = {}
for r in records:
    key = (r["tier"], r["pass"], r["ai"])
    ct[key] = ct.get(key, 0) + 1
print("tier | pass | ai | n")
for k in sorted(ct):
    print("  ", k, ct[k])

print("\n=== tier1 中 pass=N 且 ai=C 的样例（前 12）===")
n = 0
for r in records:
    if r["tier"] == 1 and r["pass"] == "N" and r["ai"] == "C":
        n += 1
        if n <= 12:
            print(f"  {r['id']} {r['file']}:{r['line']} note={r['note'][:60]}")
print("  合计:", n)

print("\n=== tier1 中 pass=Y 且 ai=N（如有）===")
n = 0
for r in records:
    if r["tier"] == 1 and r["pass"] == "Y" and r["ai"] == "N":
        n += 1
        if n <= 5:
            print(f"  {r['id']} {r['file']}:{r['line']}")
print("  合计:", n)

print("\n=== 各 tier 的 evaluator C 率 vs pass Y 率 ===")
for t in (1, 2, 3):
    sub = [r for r in records if r["tier"] == t]
    if sub:
        c = sum(1 for r in sub if r["ai"] == "C") / len(sub)
        y = sum(1 for r in sub if r["pass"] == "Y") / len(sub)
        print(f"  tier{t}: n={len(sub)}  evaluatorC={c:.0%}  passY={y:.0%}")

# 抓 tier1 样例源码片段（从 sites-pack）
pack = {it["id"]: it for it in json.load(open(f"{C1}/sites-pack.json", encoding="utf-8"))["items"]}
print("\n=== tier1 分歧样例的上下文（前 6 条）===")
n = 0
for r in records:
    if r["tier"] == 1 and r["pass"] == "N" and r["ai"] == "C":
        n += 1
        if n <= 6:
            it = pack[r["id"]]
            seg = [f"{ln}:{tx}" for ln, tx in it["context"] if abs(ln - it["line"]) <= 3]
            print(f"--- {r['id']} {r['file']}:{r['line']} kind={it['kind']}")
            print("   ", " | ".join(x.strip()[:90] for x in seg[:5]))
