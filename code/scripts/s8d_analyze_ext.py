# -*- coding: utf-8 -*-
"""S8d · 扩展实验分析（N/M/A/S 四臂，400 trials）
输出：S8-ext-汇总.json + 终端 markdown
"""
import csv
import json
import math
import os
import statistics as st

D = "/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优"
rows = list(csv.DictReader(open(os.path.join(D, "trials-ext.csv"), encoding="utf-8-sig")))
seeds = sorted(set(int(r["seed"]) for r in rows))
arms = ("N", "M", "A", "S")
print("trials:", len(rows), "| model:", rows[0].get("model"))

summary = {}
for a in arms:
    ar = [r for r in rows if r["arm"] == a]
    ok = [r for r in ar if r["status"] == "ok"]
    inv = [r for r in ar if r["status"] != "ok"]
    per_seed, costs = {}, []
    for s in seeds:
        sr = [r for r in ar if int(r["seed"]) == s]
        c = sum(float(r["cost_units"]) for r in sr)
        b = max((float(r["pp_256_ts"]) for r in sr if r["status"] == "ok"), default=0.0)
        per_seed[s] = {"cost": c, "best": b, "invalid": sum(1 for r in sr if r["status"] != "ok")}
        costs.append(c)
    summary[a] = {
        "n": len(ar), "ok": len(ok), "invalid": len(inv),
        "invalid_rate": round(len(inv) / len(ar), 4) if ar else None,
        "cost_mean": round(st.mean(costs), 3), "cost_sd": round(st.stdev(costs), 3) if len(costs) > 1 else 0.0,
        "cost_per_seed": costs,
        "best_pp_median": round(st.median([v["best"] for v in per_seed.values()]), 2),
        "exp_ub_gt_b": sum(1 for r in ok if int(r["ubatch"]) > int(r["batch"])),
        "exp_ub_gt_b_frac": round(sum(1 for r in ok if int(r["ubatch"]) > int(r["batch"])) / len(ok), 3) if ok else None,
    }

# 失败机理
fail = [r for r in rows if r["status"] != "ok"]
mech = sum(1 for r in fail if r["ctv"] == "q8_0" and r["fa"] == "off")
print(f"失败 {len(fail)}；其中 ctv=q8_0∧fa=off = {mech} ({mech/len(fail)*100:.0f}%)")

# S 臂学习轨迹
s_disc = {}
for s in seeds:
    sr = sorted([r for r in rows if r["arm"] == "S" and int(r["seed"]) == s], key=lambda x: int(x["trial"]))
    ff = None
    for r in sr:
        if r["status"] != "ok":
            ff = int(r["trial"]) + 1
            break
    s_disc[s] = ff
print("S 首次失败（第 N 次试验）:", s_disc)

tcrit = 2.776
def paired(x, y):
    d = [a - b for a, b in zip(x, y)]
    m, sd = st.mean(d), st.stdev(d)
    se = sd / math.sqrt(len(d))
    return round(m, 2), round(sd, 2), (round(m - tcrit * se, 2), round(m + tcrit * se, 2))

comp = {}
for a in ("M", "N", "S"):
    m, sd, ci = paired(summary[a]["cost_per_seed"], summary["A"]["cost_per_seed"])
    comp[f"{a}_minus_A"] = {"mean": m, "sd": sd, "ci95": ci,
                            "pct_vs_baseline": round(m / summary[a]["cost_mean"] * 100, 1)}
summary["comparisons_vs_A"] = comp
summary["failure_mechanism"] = {"total": len(fail), "ctv_q8_fa_off": mech}
summary["S_discovery_trial"] = s_disc

json.dump(summary, open(os.path.join(D, "S8-ext-汇总.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("\n| 臂 | 非法 | 成本均值±SD | 探索 ubatch>batch |")
print("|---|---|---|---|")
for a in arms:
    s = summary[a]
    print(f"| {a} | {s['invalid']}/{s['n']} ({s['invalid_rate']*100:.1f}%) | {s['cost_mean']}±{s['cost_sd']} | {s['exp_ub_gt_b']}/{s['ok']} ({s['exp_ub_gt_b_frac']*100:.0f}%) |")
print("\n对比（配对 vs A）:")
for k, v in comp.items():
    print(f"  {k}: {v['mean']}±{v['sd']} 单位, 95% CI {v['ci95']}, A 比其便宜 {v['pct_vs_baseline']}%")
print("DONE -> S8-ext-汇总.json")
