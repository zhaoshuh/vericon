# -*- coding: utf-8 -*-
"""S8 · C2 分析：三臂（N/M/A）真机调优对比
读 trials.csv → 无效率 / 成本 / 最优性能 / trials-to-target / 合法区域探索
输出：S8-汇总.json + 终端 markdown 表
"""
import csv
import json
import os
import statistics as st

D = "/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优"
import sys as _sys
CSV = _sys.argv[1] if len(_sys.argv) > 1 else (
    os.path.join(D, "trials-control.csv") if os.path.exists(os.path.join(D, "trials-control.csv"))
    else os.path.join(D, "trials.csv"))
rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
print("trials:", len(rows), "| file:", CSV)
CAL = os.path.join(D, "calibration.csv")
if os.path.exists(CAL):
    cr = list(csv.DictReader(open(CAL, encoding="utf-8-sig")))
    ppv = [float(r["pp256"]) for r in cr if r.get("pp256")]
    if ppv:
        print(f"calibration: n={len(ppv)} min={min(ppv):.1f} max={max(ppv):.1f} (环境漂移监测)")

arms = sorted(set(r["arm"] for r in rows))
seeds = sorted(set(int(r["seed"]) for r in rows))

summary = {}
for a in arms:
    ar = [r for r in rows if r["arm"] == a]
    ok = [r for r in ar if r["status"] == "ok"]
    inv = [r for r in ar if r["status"] != "ok"]
    # 每种子成本与最优
    per_seed = {}
    for s in seeds:
        sr = [r for r in ar if int(r["seed"]) == s]
        per_seed[s] = {
            "cost": sum(float(r["cost_units"]) for r in sr),
            "best": max((float(r["pp_256_ts"]) for r in sr if r["status"] == "ok"), default=0.0),
            "invalid": sum(1 for r in sr if r["status"] != "ok"),
        }
    costs = [v["cost"] for v in per_seed.values()]
    bests = [v["best"] for v in per_seed.values()]
    summary[a] = {
        "trials": len(ar), "ok": len(ok), "invalid": len(inv),
        "invalid_rate": round(len(inv) / len(ar), 4) if ar else None,
        "cost_mean": round(st.mean(costs), 3), "cost_sd": round(st.stdev(costs), 3) if len(costs) > 1 else 0,
        "best_pp_median": round(st.median(bests), 2), "best_pp_best": round(max(bests), 2),
        "per_seed": per_seed,
        # 探索行为：ok 试验里 fa/ctv/ubatch>batch 占比
        "exp_fa_on": round(sum(1 for r in ok if r["fa"] == "on") / len(ok), 3) if ok else None,
        "exp_q8": round(sum(1 for r in ok if r["ctv"] == "q8_0") / len(ok), 3) if ok else None,
        "exp_ub_gt_b": round(sum(1 for r in ok if int(r["ubatch"]) > int(r["batch"])) / len(ok), 3) if ok else None,
        "exp_ub_gt_b_n": sum(1 for r in ok if int(r["ubatch"]) > int(r["batch"])),
    }

# trials-to-target：每种子目标 = 该种子全臂最优的 98%
ttt = {}
for s in seeds:
    tgt = 0.98 * max(summary[a]["per_seed"][s]["best"] for a in arms)
    for a in arms:
        ar = [r for r in rows if r["arm"] == a and int(r["seed"]) == s]
        hit = None
        for r in sorted(ar, key=lambda x: int(x["trial"])):
            if r["status"] == "ok" and float(r["pp_256_ts"]) >= tgt:
                hit = int(r["trial"]) + 1
                break
        ttt.setdefault(a, []).append(hit if hit else 21)

summary["trials_to_target_median"] = {a: (round(st.median(v), 1) if all(x for x in v) else "not-all-reached:" + str(v))
                                      for a, v in ttt.items()}

# 关键对比
def red(a, b):  # a vs b 降幅（按均值）
    ca, cb = summary[a]["cost_mean"], summary[b]["cost_mean"]
    return round((cb - ca) / cb * 100, 1)

comp = {
    "A_vs_N_cost_reduction_pct": red("A", "N"),
    "A_vs_M_cost_reduction_pct": red("A", "M"),
    "M_vs_N_cost_reduction_pct": red("M", "N"),
    "invalid_rate_N": summary["N"]["invalid_rate"], "invalid_rate_M": summary["M"]["invalid_rate"],
    "invalid_rate_A": summary["A"]["invalid_rate"],
}
summary["comparisons"] = comp
json.dump(summary, open(os.path.join(D, "S8-汇总.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("\n| 臂 | 无效率 | 成本均值±SD | 最优 pp 中位 | ubatch>batch 探索 |")
print("|---|---|---|---|---|")
for a in arms:
    s = summary[a]
    print(f"| {a} | {s['invalid_rate']*100:.1f}% | {s['cost_mean']}±{s['cost_sd']} | {s['best_pp_median']} | "
          f"{s['exp_ub_gt_b_n']}/{s['ok']} ({s['exp_ub_gt_b']*100:.0f}%) |")
print("\n", json.dumps(comp, ensure_ascii=False))
print("trials-to-target:", json.dumps(summary["trials_to_target_median"], ensure_ascii=False))
print("DONE -> S8-汇总.json")
