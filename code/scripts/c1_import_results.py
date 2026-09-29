# -*- coding: utf-8 -*-
"""C1 · 独立盲标回传导入（AI 第三遍；非人类）：一致率/κ + 人类标签下的召回复核
用法：把回传的 c1_results.csv 放到 实验记录/C1-人类盲标/ 后运行本脚本。
"""
import csv
import json
import os
import re
import sys

BASE = "/mnt/f/文献/AgentOps/实验记录"
C1 = os.path.join(BASE, "C1-人类盲标")
GRAPH = os.path.join(BASE, "约束图-v1-ext.json")
CSV = os.path.join(C1, "c1_results.csv")
TIER_POP = {1: 244, 2: 119, 3: 2766}  # 论文口径的层规模

if not os.path.exists(CSV):
    print("缺少 c1_results.csv —— 请先把回传文件放到:", C1)
    sys.exit(1)

pack = json.load(open(os.path.join(C1, "sites-pack.json"), encoding="utf-8"))["items"]
by_id = {it["id"]: it for it in pack}

# ---- 捕获索引（从最终约束图现算） ----
gd = json.load(open(GRAPH, encoding="utf-8"))


def ev_pairs(ev):
    if isinstance(ev, dict):
        yield ev.get("file"), ev.get("line")
    elif isinstance(ev, list):
        for it in ev:
            yield from ev_pairs(it)
    elif isinstance(ev, str):
        m = re.search(r"([\w./\\-]+\.py):(\d+)", ev)
        if m:
            yield m.group(1).replace("\\", "/"), int(m.group(2))


cap_index = {}
for n in gd["nodes"]:
    for f, l in ev_pairs(n.get("evidence")):
        if f and l:
            cap_index.setdefault(f.replace("\\", "/").lstrip("./"), []).append((int(l), n.get("id")))


def capture(f, l):
    ex = pm1 = False
    ids = []
    for (cl, cid) in cap_index.get(f, []):
        if cl == l:
            ex = pm1 = True
            ids.append(cid)
        elif abs(cl - l) <= 1:
            pm1 = True
            ids.append(cid)
    return ex, pm1, ids


# ---- AI 既有标签（两批） ----
ai = {}
for fn in ("P1b-标注结果.json", "P1b-标注结果2.json"):
    p = os.path.join(BASE, fn)
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    rows = d.get("rows") or d.get("labels") or []
    if isinstance(rows, dict):
        rows = list(rows.values())
    for r in rows:
        f = str(r.get("file", "")).replace("\\", "/")
        ai[(f, int(r.get("line", -1)))] = str(r.get("label", "")).upper()[:1]
print("AI 标签条数:", len(ai), "| 值分布:", {v: sum(1 for x in ai.values() if x == v) for v in set(ai.values())})

# ---- 人类结果 ----
human = {}
def _norm_v(x):
    s = (x or "").strip()
    m = {"是": "Y", "否": "N", "不确定": "U", "yes": "Y", "no": "N", "unsure": "U",
         "y": "Y", "n": "N", "u": "U", "c": "Y"}
    return m.get(s.lower(), s[:1].upper() if s else "")

with open(CSV, encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        human[r["id"]] = {"v": _norm_v(r["verdict"]), "n": r.get("note", "")}

pairs = []  # (tier, humanY?, captured_pm1, captured_exact, agree?)
recs = []
for hid, it in by_id.items():
    h = human.get(hid, {})
    v = h.get("v", "")
    ex, pm1, ids = capture(it["file"], it["line"])
    a = ai.get((it["file"], it["line"]), "")
    hv = {"Y": "C", "N": "N"}.get(v, v)
    recs.append({"id": hid, "tier": it["tier"], "file": it["file"], "line": it["line"],
                 "pass": v, "ai": a, "captured_exact": ex, "captured_pm1": pm1, "graph_ids": ids,
                 "note": h.get("n", "")})

done = [r for r in recs if r["pass"] in ("Y", "N", "U")]
print(f"\n已标注 {len(done)}/{len(recs)}  Y={sum(1 for r in done if r['pass']=='Y')} "
      f"N={sum(1 for r in done if r['pass']=='N')} U={sum(1 for r in done if r['pass']=='U')}")

# 一致率与 κ（仅 Y/N 对 C/N；Y↔C 映射后比较）
fr = [r for r in recs if r["pass"] in ("Y", "N") and r["ai"] in ("C", "N")]
both = [({"Y": "C", "N": "N"}[r["pass"]], r["ai"]) for r in fr]
n = len(both)
kappa = po = float("nan")
if n:
    po = sum(1 for h, a in both if h == a) / n
    pe = ((sum(1 for h, a in both if h == "C") / n) * (sum(1 for h, a in both if a == "C") / n) +
          (sum(1 for h, a in both if h == "N") / n) * (sum(1 for h, a in both if a == "N") / n))
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    print(f"一致率（n={n}）: {po*100:.1f}%  Cohen's κ = {kappa:.3f}")
    for t in (1, 2, 3):
        idx = [i for i, r in enumerate(fr) if r["tier"] == t]
        if idx:
            sub = [both[i] for i in idx]
            print(f"  tier{t}: 一致 {sum(1 for h,a in sub if h==a)}/{len(sub)}")

# 人类标签下的召回（层等权 + 精确/±1）
tier_rates = {}
for t in (1, 2, 3):
    sub = [r for r in recs if r["tier"] == t and r["pass"] == "Y"]
    if sub:
        tier_rates[t] = {"n": len(sub), "pm1": sum(1 for r in sub if r["captured_pm1"]) / len(sub),
                         "exact": sum(1 for r in sub if r["captured_exact"]) / len(sub)}
if tier_rates:
    ew_pm1 = sum(v["pm1"] for v in tier_rates.values()) / len(tier_rates)
    ew_ex = sum(v["exact"] for v in tier_rates.values()) / len(tier_rates)
    wsum = sum(TIER_POP[t] for t in tier_rates)
    dw_pm1 = sum(v["pm1"] * TIER_POP[t] for t, v in tier_rates.items()) / wsum
    dw_ex = sum(v["exact"] * TIER_POP[t] for t, v in tier_rates.items()) / wsum
    print("\n独立盲标(AI第三遍)标签下的召回（对照论文 71.9%/87.2%）：")
    print(f"  层等权: exact {ew_ex*100:.1f}% / ±1 {ew_pm1*100:.1f}%")
    print(f"  设计加权: exact {dw_ex*100:.1f}% / ±1 {dw_pm1*100:.1f}%")
    for t, v in tier_rates.items():
        print(f"  tier{t}: n={v['n']}  exact {v['exact']*100:.0f}% / ±1 {v['pm1']*100:.0f}%")

json.dump({"records": recs, "tier_rates": tier_rates,
           "agreement": {"n": n, "raw": round(po, 4) if n else None, "kappa": round(kappa, 4) if n else None},
           "pass_recall": {"equal_weight": {"exact": ew_ex if tier_rates else None, "pm1": ew_pm1 if tier_rates else None},
                            "design_weighted": {"exact": dw_ex if tier_rates else None, "pm1": dw_pm1 if tier_rates else None}}},
          open(os.path.join(C1, "C1-导入结果.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n已保存:", os.path.join(C1, "C1-导入结果.json"))
