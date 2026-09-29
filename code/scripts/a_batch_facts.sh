#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
import json, re
from collections import Counter, defaultdict

BASE = "/mnt/f/文献/AgentOps/实验记录"

# ---------- 1) 召回：三种加权 ----------
rows = []
for fn in ("P1b-标注结果.json", "P1b-标注结果2.json"):
    d = json.load(open(f"{BASE}/{fn}", encoding="utf-8"))
    rows += d.get("rows", [])
print("labels:", len(rows))
N = {1: 244, 2: 119, 3: 2766}  # 候选站点数（per tier）
agg = defaultdict(lambda: {"n": 0, "c": 0, "ce": 0, "cp": 0})
for r in rows:
    t = int(r["tier"]); a = agg[t]
    a["n"] += 1
    if str(r["label"]).upper().startswith("C"):
        a["c"] += 1
    if r.get("captured_exact"): a["ce"] += 1
    if r.get("captured_pm1"): a["cp"] += 1
print("\ntier | n | C(真约束) | r_exact | r_pm1 | p=C/n")
for t in (1, 2, 3):
    a = agg[t]
    print(f"  {t} | {a['n']} | {a['c']} | {a['ce']/a['c']:.3f} | {a['cp']/a['c']:.3f} | {a['c']/a['n']:.3f}")

eq_ex = sum(agg[t]['ce']/agg[t]['c'] for t in (1,2,3))/3
eq_pm = sum(agg[t]['cp']/agg[t]['c'] for t in (1,2,3))/3
sw_ex = sum(N[t]*agg[t]['ce']/agg[t]['c'] for t in (1,2,3))/sum(N.values())
sw_pm = sum(N[t]*agg[t]['cp']/agg[t]['c'] for t in (1,2,3))/sum(N.values())
cw_w  = {t: N[t]*agg[t]['c']/agg[t]['n'] for t in (1,2,3)}
cw_ex = sum(cw_w[t]*agg[t]['ce']/agg[t]['c'] for t in (1,2,3))/sum(cw_w.values())
cw_pm = sum(cw_w[t]*agg[t]['cp']/agg[t]['c'] for t in (1,2,3))/sum(cw_w.values())
print(f"\n等权(equal-weight)                 : exact {eq_ex*100:.1f}%  pm1 {eq_pm*100:.1f}%")
print(f"站点加权(site count, N_t)          : exact {sw_ex*100:.1f}%  pm1 {sw_pm*100:.1f}%")
print(f"约束加权(constraint count, N_t*p_t): exact {cw_ex*100:.1f}%  pm1 {cw_pm*100:.1f}%")

# ---------- 2) 约束图成环 ----------
g = json.load(open(f"{BASE}/约束图-v1-ext.json", encoding="utf-8"))
adj = defaultdict(set)
for n in g["nodes"]:
    if n.get("type") == "implication":
        ps = n.get("params") or []
        if len(ps) >= 2:
            adj[ps[0]].add(ps[1])
# Tarjan SCC
index, low, on, stack, sccs = {}, {}, set(), [], []
counter = [0]
def strong(v):
    index[v] = low[v] = counter[0]; counter[0] += 1
    stack.append(v); on.add(v)
    for w in adj.get(v, ()):
        if w not in index:
            strong(w); low[v] = min(low[v], low[w])
        elif w in on:
            low[v] = min(low[v], index[w])
    if low[v] == index[v]:
        comp = []
        while True:
            w = stack.pop(); on.discard(w); comp.append(w)
            if w == v: break
        sccs.append(comp)
import sys
sys.setrecursionlimit(100000)
for v in list(adj):
    if v not in index:
        strong(v)
cyc = [c for c in sccs if len(c) > 1]
print(f"\nimplication 参数边: {sum(len(v) for v in adj.values())}; SCC 总数 {len(sccs)}; 含环 SCC {len(cyc)}; 最大环 {max((len(c) for c in cyc), default=0)}")
print("环示例:", [c[:4] for c in cyc[:3]])
PYEOF
echo ""
echo "=== 定理/审计/限制节原文 ==="
T=/mnt/f/文献/AgentOps/论文/latex/main.tex
grep -n 'Reliability of confirmation\|Zero-violation property\|Cumulative: \|130 constraint-audits' "$T" | head -6
