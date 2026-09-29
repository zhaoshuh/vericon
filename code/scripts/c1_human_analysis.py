# -*- coding: utf-8 -*-
"""C1 人类标注验收与分析
- 读取 F:\Download\c1_results.csv（人类回传）
- 存档到 实验记录/C1-人类盲标/人类标注/
- 与评测者标签、AI 第三遍标签对比；计算人类标签下的召回（等权/站点加权/约束加权）
输出：C1-人类标注-结果.json
"""
import csv
import json
import os
import re
from collections import Counter

SRC = "/mnt/f/Download/c1_results.csv"
DEST_DIR = "/mnt/f/文献/AgentOps/实验记录/C1-人类盲标/人类标注"
BASE = "/mnt/f/文献/AgentOps/实验记录"
C1 = f"{BASE}/C1-人类盲标"
GRAPH = f"{BASE}/约束图-v1-ext.json"
POP = {1: 244, 2: 119, 3: 2766}

os.makedirs(DEST_DIR, exist_ok=True)
raw = open(SRC, encoding="utf-8-sig").read()
open(f"{DEST_DIR}/c1_results-human.csv", "w", encoding="utf-8", newline="").write(raw)
print("原始文件已存档 ->", f"{DEST_DIR}/c1_results-human.csv")

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
print("行数:", len(rows), "| 列:", list(rows[0].keys()))


def norm(x):
    s = (x or "").strip()
    m = {"是": "Y", "否": "N", "不确定": "U", "yes": "Y", "no": "N", "unsure": "U", "c": "Y"}
    return m.get(s.lower(), s[:1].upper() if s else "")


human = {}
for r in rows:
    human[r["id"]] = {"v": norm(r.get("verdict")), "n": (r.get("note") or "").strip(),
                      "tier": int(r.get("tier") or 0), "file": r.get("file", ""), "line": int(r.get("line") or 0)}
dist = Counter(h["v"] for h in human.values())
print("verdict 分布:", dict(dist))
bad = [k for k, h in human.items() if h["v"] not in ("Y", "N", "U")]
print("异常值:", bad[:5] if bad else "无")
notes = [(k, h["n"]) for k, h in human.items() if h["n"]]
print("带备注条数:", len(notes), notes[:3] if notes else "")

# ---------- 捕获索引（从最终约束图现算） ----------
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


cap = {}
for n in gd["nodes"]:
    for f, l in ev_pairs(n.get("evidence")):
        if f and l:
            cap.setdefault(f.replace("\\", "/").lstrip("./"), []).append(int(l))


def captured(f, l, tol=1):
    return any(abs(cl - l) <= tol for cl in cap.get(f, []))


# ---------- 评测者标签 / AI 第三遍标签 ----------
ai_eval = {}
for fn in ("P1b-标注结果.json", "P1b-标注结果2.json"):
    d = json.load(open(f"{BASE}/{fn}", encoding="utf-8"))
    for r in d.get("rows", []):
        ai_eval[(str(r["file"]).replace("\\", "/"), int(r["line"]))] = str(r["label"]).upper()[:1]
ai_pass = {}
for r in csv.DictReader(open(f"{C1}/c1_results.csv", encoding="utf-8-sig")):
    ai_pass[r["id"]] = norm(r["verdict"])

recs = []
for hid, h in human.items():
    a_eval = ai_eval.get((h["file"], h["line"]), "")
    recs.append({"id": hid, "tier": h["tier"], "file": h["file"], "line": h["line"],
                 "human": h["v"], "note": h["n"], "ai_eval": a_eval, "ai_pass": ai_pass.get(hid, ""),
                 "captured": captured(h["file"], h["line"])})


def agree_kappa(pairs):
    both = [(a, b) for a, b in pairs if a in ("Y", "N") and b in ("Y", "N")]
    if not both:
        return None
    n = len(both)
    po = sum(1 for a, b in both if a == b) / n
    pa = sum(1 for a, b in both if a == "Y") / n
    pb = sum(1 for a, b in both if b == "Y") / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return {"n": n, "raw": round(po, 4), "kappa": round(k, 4)}


# 人类 vs 评测者（Y↔C 映射）
hv = [(r["human"], {"C": "Y", "N": "N"}.get(r["ai_eval"], "")) for r in recs]
k_eval = agree_kappa(hv)
# 人类 vs AI 第三遍
k_pass = agree_kappa([(r["human"], r["ai_pass"]) for r in recs])
print("\n人类 vs 评测者标签:", k_eval)
print("人类 vs AI 第三遍 :", k_pass)

# ---------- 人类标签下的召回 ----------
tiers = {}
for t in (1, 2, 3):
    sub = [r for r in recs if r["tier"] == t]
    y = [r for r in sub if r["human"] == "Y"]
    tiers[t] = {"n_sites": len(sub), "n_Y": len(y),
                "precision": round(len(y) / len(sub), 4) if sub else None,
                "recall": round(sum(1 for r in y if r["captured"]) / len(y), 4) if y else None}
eq = sum(tiers[t]["recall"] for t in tiers if tiers[t]["recall"]) / len([t for t in tiers if tiers[t]["recall"]])
sw = sum(POP[t] * tiers[t]["recall"] for t in tiers if tiers[t]["recall"]) / sum(POP[t] for t in tiers if tiers[t]["recall"])
w = {t: POP[t] * tiers[t]["precision"] for t in tiers if tiers[t]["recall"]}
cw = sum(w[t] * tiers[t]["recall"] for t in w) / sum(w.values())
print(f"\n人类标签下召回（±1 行）: 等权 {eq*100:.1f}% | 站点加权 {sw*100:.1f}% | 约束加权 {cw*100:.1f}%")
for t in (1, 2, 3):
    print(f"  tier{t}: Y={tiers[t]['n_Y']}/{tiers[t]['n_sites']}  precision={tiers[t]['precision']}  recall={tiers[t]['recall']}")

out = {"source": SRC, "n": len(recs), "dist": dict(dist), "notes": notes,
       "agreement_human_vs_evaluator": k_eval, "agreement_human_vs_ai_pass": k_pass,
       "tiers": tiers, "recall_pm1": {"equal_weight": round(eq, 4), "site_weighted": round(sw, 4),
                                      "constraint_weighted": round(cw, 4)},
       "records": recs}
json.dump(out, open(f"{C1}/C1-人类标注-结果.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n已保存:", f"{C1}/C1-人类标注-结果.json")
