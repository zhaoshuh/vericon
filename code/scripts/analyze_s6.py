# -*- coding: utf-8 -*-
"""S6 分析：SCOOT 式 S 臂 vs N/M/A（5d @ qps12，种子 1-20）

口径与 S5/analyze_p4 一致：成本 = Σ experiment_units；非法 = 失败 ∪ 违反约束；目标 = 组内全局最优×0.9。
输出：实验记录/S6-结果.csv、S6-报告.md
"""
import csv
import glob
import json
import os
import re
import statistics
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OPT = r"F:\文献\AgentOps\实验记录\optuna"
OUT_CSV = r"F:\文献\AgentOps\实验记录\S6-结果.csv"
OUT_MD = r"F:\文献\AgentOps\实验记录\S6-报告.md"


def read_study(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def bootstrap_ci_paired(a, b, n_boot=5000, alpha=0.05, seed=42):
    import random
    rng = random.Random(seed)
    n = min(len(a), len(b))
    if n < 2:
        return 0.0, 0.0
    reds = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            i = rng.randrange(n)
            x, y = a[i], b[i]
            s += (x - y) / x if x else 0.0
        reds.append(s / n)
    reds.sort()
    return reds[int(alpha / 2 * n_boot)], reds[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]


def main():
    studies = {}
    for d in sorted(glob.glob(os.path.join(OPT, "s5-*-seed*"))) + sorted(glob.glob(os.path.join(OPT, "s6-S-seed*"))):
        base = os.path.basename(d)
        m = re.match(r"s5-(N|M|A)-seed(\d+)$", base) or re.match(r"s6-S-seed(\d+)$", base)
        if not m:
            continue
        if base.startswith("s6-"):
            arm, seed = "S", int(m.group(1))
        else:
            arm, seed = m.group(1), int(m.group(2))
        csv_path = os.path.join(d, "trials.csv")
        if os.path.exists(csv_path):
            studies[(arm, seed)] = read_study(csv_path)

    if not studies:
        print("无数据")
        return

    best_global = 0.0
    for trials in studies.values():
        for t in trials:
            best_global = max(best_global, to_float(t.get("value")))
    target = best_global * 0.9

    rows = []
    for (arm, seed), trials in sorted(studies.items()):
        n = len(trials)
        n_invalid = sum(
            1 for t in trials
            if ((t.get("user_attrs_status") or "ok") != "ok")
            or str(t.get("user_attrs_constraint_violated", "")).lower() == "true"
        )
        cost = sum(to_float(t.get("user_attrs_experiment_units"), 1.0) for t in trials)
        values = [to_float(t.get("value")) for t in trials]
        best = max(values) if values else 0.0
        ttt = ""
        for i, v in enumerate(values):
            if v >= target:
                ttt = i + 1
                break
        floor_final = ""
        if arm == "S":
            floors = [to_float(t.get("user_attrs_learned_floor"), 0) for t in trials]
            floor_final = max(floors) if floors else 0
        rows.append({
            "arm": arm, "seed": seed, "n_trials": n, "n_invalid": n_invalid,
            "invalid_rate": round(n_invalid / n, 4) if n else 0.0,
            "cumulative_cost": round(cost, 2), "best_goodput": round(best, 4),
            "trials_to_target": ttt if ttt != "" else "",
            "learned_floor_final": floor_final,
        })

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def vals(arm, key):
        return [r[key] for r in rows if r["arm"] == arm and isinstance(r[key], (int, float))]

    def agg(arm, key):
        v = vals(arm, key)
        return f"{statistics.mean(v):.2f} ± {statistics.stdev(v):.2f}" if len(v) > 1 else (f"{v[0]:.2f}" if v else "—")

    def ttt_agg(arm):
        v = [r["trials_to_target"] for r in rows if r["arm"] == arm and r["trials_to_target"] != ""]
        if not v:
            return "未达标"
        return f"{statistics.mean(v):.2f} ± {statistics.stdev(v):.2f}" if len(v) > 1 else f"{v[0]:.2f}"

    def paired(arm_a, arm_b, key="cumulative_cost"):
        a = {r["seed"]: r[key] for r in rows if r["arm"] == arm_a}
        b = {r["seed"]: r[key] for r in rows if r["arm"] == arm_b}
        common = sorted(set(a) & set(b))
        if len(common) < 2:
            return "—", None
        va = [a[s] for s in common]
        vb = [b[s] for s in common]
        mean = statistics.mean((x - y) / x for x, y in zip(va, vb))
        lo, hi = bootstrap_ci_paired(va, vb)
        return f"{mean:.1%} [{lo:.1%}, {hi:.1%}]（n={len(common)}）", mean

    md = [
        "# S6 · SCOOT 式基线臂（S）对照报告",
        "",
        f"> 设定：5d @ qps=12，种子 1–20 × 30 trials；目标 = 全局最优×0.9（{target:.3f}）；口径同 S5。",
        "> S 臂 = 人工规则（mtib≥mns）+ **在线边界学习**（失败后抬高 mtib 下界）。",
        "",
        "| 臂 | 累计成本（均值±std） | 非法率 | 最优 goodput | trials-to-target |",
        "|---|---|---|---|---|",
    ]
    for arm, label in (("N", "N 无约束"), ("S", "S SCOOT 式（在线学习）"), ("M", "M 人工约束"), ("A", "A 自动约束")):
        if vals(arm, "cumulative_cost"):
            md.append(f"| {label} | {agg(arm, 'cumulative_cost')} | {agg(arm, 'invalid_rate')} | "
                      f"{agg(arm, 'best_goodput')} | {ttt_agg(arm)} |")
    md += ["", "**配对成本降低（bootstrap 95% CI）**", "",
           "| 对照 | 降幅 |", "|---|---|"]
    for a, b, lab in (("N", "S", "N → S"), ("N", "A", "N → A"), ("S", "A", "**S → A（自动抽取的增量价值）**")):
        r, _ = paired(a, b)
        md.append(f"| {lab} | {r} |")
    s_floors = [r["learned_floor_final"] for r in rows if r["arm"] == "S" and isinstance(r["learned_floor_final"], (int, float))]
    if s_floors:
        md += ["", f"- S 臂最终学习下界：均值 {statistics.mean(s_floors):.0f} ± {statistics.stdev(s_floors):.0f}（真实负载约束 ≈ 1024）",
               f"- S 臂平均非法率 {statistics.mean(vals('S', 'invalid_rate')):.1%}（学习过程付出的代价）vs A 臂 0%"]
    md += ["", "*生成：2026-09-28 ｜ 明细见 `S6-结果.csv`*"]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))

    print(f"studies={len(rows)}")
    for arm in ("N", "S", "M", "A"):
        if vals(arm, "cumulative_cost"):
            print(f"  {arm}: cost={agg(arm, 'cumulative_cost')} invalid={agg(arm, 'invalid_rate')} ttt={ttt_agg(arm)}")
    for a, b, lab in (("N", "S", "N->S"), ("N", "A", "N->A"), ("S", "A", "S->A")):
        r, _ = paired(a, b)
        print(f"  {lab}: {r}")
    print("->", OUT_MD)


if __name__ == "__main__":
    main()
