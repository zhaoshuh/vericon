# -*- coding: utf-8 -*-
"""P4 结果分析：维度扩展（2d / 5d / 6d）+ 负载稳健性（qps 8/12/16）

数据源：实验记录/optuna/{s5-*-seed*, p4-*}/trials.csv
输出：
  实验记录/P4-结果.csv     每 study 一行
  实验记录/P4-结果.json    结构化汇总
  实验记录/P4-报告.md      论文口径报告
用法: python analyze_p4.py
"""
import csv
import datetime
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
OUT_CSV = r"F:\文献\AgentOps\实验记录\P4-结果.csv"
OUT_JSON = r"F:\文献\AgentOps\实验记录\P4-结果.json"
OUT_MD = r"F:\文献\AgentOps\实验记录\P4-报告.md"

SEEDS_CURVE = range(1, 11)          # 维度/负载曲线的配对种子（5d 用 s5 的 1-10 子集）
BLOCKS_PER_SEQ = 64                 # ceil(1024 / 16)


def parse_study(name):
    m = re.match(r"s5-(N|M|A)-seed(\d+)$", name)
    if m:
        return {"mode": "5d", "qps": 12.0, "arm": m.group(1), "seed": int(m.group(2))}
    m = re.match(r"p4-(2d|5d|6d)-q(\d+)-(N|M|A)-s(\d+)$", name)
    if m:
        return {"mode": m.group(1), "qps": float(m.group(2)), "arm": m.group(3), "seed": int(m.group(4))}
    return None


def read_study(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def bootstrap_ci(vals, n_boot=5000, alpha=0.05, seed=42):
    import random
    rng = random.Random(seed)
    n = len(vals)
    if n < 2:
        v = vals[0] if vals else 0.0
        return v, v
    means = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += vals[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    return means[int(alpha / 2 * n_boot)], means[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]


def bootstrap_ci_paired(vals_a, vals_b, n_boot=5000, alpha=0.05, seed=42):
    import random
    rng = random.Random(seed)
    n = min(len(vals_a), len(vals_b))
    if n < 2:
        return 0.0, 0.0
    reds = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            i = rng.randrange(n)
            a, b = vals_a[i], vals_b[i]
            s += (a - b) / a if a else 0.0
        reds.append(s / n)
    reds.sort()
    return reds[int(alpha / 2 * n_boot)], reds[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]


def main():
    rows = []
    for d in sorted(glob.glob(os.path.join(OPT, "*"))):
        if not os.path.isdir(d):
            continue
        meta = parse_study(os.path.basename(d))
        if meta is None:
            continue
        csv_path = os.path.join(d, "trials.csv")
        if not os.path.exists(csv_path):
            continue
        trials = read_study(csv_path)
        if not trials:
            continue
        n = len(trials)
        n_invalid = sum(
            1 for t in trials
            if ((t.get("user_attrs_status") or "ok") != "ok")
            or str(t.get("user_attrs_constraint_violated", "")).lower() == "true"
        )
        cost = sum(to_float(t.get("user_attrs_experiment_units"), 1.0) for t in trials)
        values = [to_float(t.get("value")) for t in trials]
        best = max(values) if values else 0.0
        # 6d：容量规则（num_blocks ≥ 64 × mns）违反率 + 最优 trial 的 num_blocks
        nb_viol = nb_total = 0
        best_trial_nb = None
        if meta["mode"] == "6d":
            best_i = values.index(best) if values else -1
            for i, t in enumerate(trials):
                nb = t.get("params_num_blocks")
                mns = t.get("params_max_num_seqs")
                if nb in (None, "") or mns in (None, ""):
                    continue
                nb_total += 1
                if to_float(nb) < BLOCKS_PER_SEQ * to_float(mns):
                    nb_viol += 1
            if best_i >= 0:
                best_trial_nb = trials[best_i].get("params_num_blocks")
        rows.append({
            "study": os.path.basename(d), **meta, "n_trials": n,
            "n_invalid": n_invalid,
            "invalid_rate": round(n_invalid / n, 4) if n else 0.0,
            "cumulative_cost": round(cost, 2),
            "best_goodput": round(best, 4),
            "nb_capacity_violations": nb_viol,
            "nb_trials_with_nb": nb_total,
            "best_trial_num_blocks": best_trial_nb,
        })

    if not rows:
        print("无 p4/s5 study 数据")
        return

    # trials-to-target：以 (mode, qps) 组内全局最优 × 0.9 为目标
    group_best = {}
    for r in rows:
        k = (r["mode"], r["qps"])
        group_best[k] = max(group_best.get(k, 0.0), r["best_goodput"])
    for r in rows:
        target = group_best[(r["mode"], r["qps"])] * 0.9
        trials = read_study(os.path.join(OPT, r["study"], "trials.csv"))
        ttt = ""
        for i, t in enumerate(trials):
            if to_float(t.get("value")) >= target:
                ttt = i + 1
                break
        r["trials_to_target"] = ttt

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def sub(mode=None, qps=None, seeds=None):
        out = rows
        if mode:
            out = [r for r in out if r["mode"] == mode]
        if qps is not None:
            out = [r for r in out if abs(r["qps"] - qps) < 1e-9]
        if seeds is not None:
            out = [r for r in out if r["seed"] in seeds]
        return out

    def arm_vals(rs, arm, key):
        return [r[key] for r in rs if r["arm"] == arm and isinstance(r[key], (int, float))]

    def agg(rs, arm, key):
        v = arm_vals(rs, arm, key)
        if not v:
            return "—"
        return f"{statistics.mean(v):.2f} ± {statistics.stdev(v):.2f}" if len(v) > 1 else f"{v[0]:.2f}"

    def paired_red(rs, arm_a, arm_b, key="cumulative_cost"):
        a = {r["seed"]: r[key] for r in rs if r["arm"] == arm_a}
        b = {r["seed"]: r[key] for r in rs if r["arm"] == arm_b}
        common = sorted(set(a) & set(b))
        va = [a[s] for s in common]
        vb = [b[s] for s in common]
        if len(va) < 2:
            return "—", None, None
        mean = statistics.mean((x - y) / x for x, y in zip(va, vb))
        lo, hi = bootstrap_ci_paired(va, vb)
        return f"{mean:.1%} [{lo:.1%}, {hi:.1%}]（n={len(common)}）", mean, (lo, hi)

    md = [
        "# P4 · 维度扩展与负载稳健性（报告）",
        "",
        f"> 数据：`实验记录/optuna/` 中 `s5-*`（5d@qps12）与 `p4-*`（2d/6d@qps12；5d@qps8/16）；",
        f"> 口径与 S5 一致：成本 = Σ experiment_units（合法=1，非法=1+c，主口径 c=3）；非法 = 失败 ∪ 违反约束；配对种子 1–10。",
        "",
        "## A. 维度曲线（qps=12，种子 1–10）",
        "",
        "| 空间 | 臂 | 累计成本（均值±std） | 非法率 | 最优 goodput |",
        "|---|---|---|---|---|",
    ]
    for mode in ("2d", "5d", "6d"):
        rs = sub(mode=mode, qps=12.0, seeds=SEEDS_CURVE)
        if not rs:
            continue
        for arm, label in (("N", "N 无约束"), ("M", "M 人工约束"), ("A", "A 自动约束")):
            md.append(f"| {mode} | {label} | {agg(rs, arm, 'cumulative_cost')} | "
                      f"{agg(rs, arm, 'invalid_rate')} | {agg(rs, arm, 'best_goodput')} |")
    md += ["", "**成本降低（配对 bootstrap 95% CI）**", "",
           "| 空间 | N→M | N→A |", "|---|---|---|"]
    for mode in ("2d", "5d", "6d"):
        rs = sub(mode=mode, qps=12.0, seeds=SEEDS_CURVE)
        if not rs:
            continue
        nm, _, _ = paired_red(rs, "N", "M")
        na, _, _ = paired_red(rs, "N", "A")
        md.append(f"| {mode} | {nm} | {na} |")

    md += ["", "## B. 负载稳健性（5d，种子 1–10）", "",
           "| qps | 臂 | 累计成本（均值±std） | 非法率 | 最优 goodput |", "|---|---|---|---|---|"]
    for q in (8.0, 12.0, 16.0):
        rs = sub(mode="5d", qps=q, seeds=SEEDS_CURVE)
        if not rs:
            continue
        for arm, label in (("N", "N 无约束"), ("M", "M 人工约束"), ("A", "A 自动约束")):
            md.append(f"| {q:g} | {label} | {agg(rs, arm, 'cumulative_cost')} | "
                      f"{agg(rs, arm, 'invalid_rate')} | {agg(rs, arm, 'best_goodput')} |")
    md += ["", "**成本降低（配对 bootstrap 95% CI）**", "",
           "| qps | N→M | N→A |", "|---|---|---|"]
    for q in (8.0, 12.0, 16.0):
        rs = sub(mode="5d", qps=q, seeds=SEEDS_CURVE)
        if not rs:
            continue
        nm, _, _ = paired_red(rs, "N", "M")
        na, _, _ = paired_red(rs, "N", "A")
        md.append(f"| {q:g} | {nm} | {na} |")

    # C. 6d：num_blocks 容量约束
    rs6 = sub(mode="6d", qps=12.0, seeds=SEEDS_CURVE)
    md += ["", "## C. 6d：num_blocks 容量约束（num_blocks ≥ 64 × mns）", ""]
    if rs6:
        for arm, label in (("N", "N 无约束"), ("M", "M 人工约束"), ("A", "A 自动约束")):
            v = [r for r in rs6 if r["arm"] == arm and r["nb_trials_with_nb"]]
            if not v:
                continue
            viol = sum(r["nb_capacity_violations"] for r in v)
            tot = sum(r["nb_trials_with_nb"] for r in v)
            md.append(f"- **{label}**：容量规则违反 {viol}/{tot}（{viol/tot:.1%}）；"
                      f"最优 trial num_blocks 均值 {statistics.mean([to_float(r['best_trial_num_blocks']) for r in v]):.0f}")
    else:
        md.append("（6d 数据尚未产生）")

    md += ["", "## 汇总 JSON", "", "```json",
           json.dumps({
               "dim_curve_q12": {mode: {
                   "N_cost": agg(sub(mode=mode, qps=12.0, seeds=SEEDS_CURVE), "N", "cumulative_cost"),
                   "A_cost": agg(sub(mode=mode, qps=12.0, seeds=SEEDS_CURVE), "A", "cumulative_cost"),
                   "N_to_A": paired_red(sub(mode=mode, qps=12.0, seeds=SEEDS_CURVE), "N", "A")[0],
               } for mode in ("2d", "5d", "6d") if sub(mode=mode, qps=12.0, seeds=SEEDS_CURVE)},
               "load_curve_5d": {str(q): {
                   "N_to_A": paired_red(sub(mode="5d", qps=q, seeds=SEEDS_CURVE), "N", "A")[0],
               } for q in (8.0, 12.0, 16.0) if sub(mode="5d", qps=q, seeds=SEEDS_CURVE)},
           }, ensure_ascii=False, indent=2),
           "```", "",
           f"*生成：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ 每 study 明细见 `P4-结果.csv`*"]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    json.dump({"rows": rows, "group_best": {f"{k[0]}@{k[1]}": v for k, v in group_best.items()}},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"studies={len(rows)}")
    print("->", OUT_CSV)
    print("->", OUT_MD)
    for mode in ("2d", "5d", "6d"):
        rs = sub(mode=mode, qps=12.0, seeds=SEEDS_CURVE)
        if rs:
            na = paired_red(rs, "N", "A")
            print(f"  {mode}@q12: N={agg(rs,'N','cumulative_cost')} A={agg(rs,'A','cumulative_cost')} N→A={na[0]}")


if __name__ == "__main__":
    main()
