# -*- coding: utf-8 -*-
"""S5 结果分析：读 实验记录/optuna/s5-{arm}-seed*/trials.csv → 汇总对比

输出:
  实验记录/对比结果.csv     （每 seed 一行：成本 / 非法率 / 最优值 / trials-to-target）
  实验记录/S5-汇总.md       （三臂汇总：均值±std + 空间缩减）
用法: python analyze_s5.py [--target-ratio 0.9]
"""
import csv
import glob
import math
import os
import re
import statistics
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OPTUNA_DIR = r"F:\文献\AgentOps\实验记录\optuna"
OUT_CSV = r"F:\文献\AgentOps\实验记录\对比结果.csv"
OUT_MD = r"F:\文献\AgentOps\实验记录\S5-汇总.md"


def read_study(path):
    trials = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            trials.append(row)
    return trials


def to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def bootstrap_ci(vals, n_boot=5000, alpha=0.05, seed=42):
    """bootstrap 均值 95% CI"""
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
    lo = means[int(alpha / 2 * n_boot)]
    hi = means[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]
    return lo, hi


def bootstrap_ci_paired(vals_a, vals_b, n_boot=5000, alpha=0.05, seed=42):
    """配对 bootstrap：(a_i - b_i)/a_i 的 95% CI（同种子配对）"""
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
    target_ratio = 0.9
    if "--target-ratio" in sys.argv:
        target_ratio = float(sys.argv[sys.argv.index("--target-ratio") + 1])

    studies = {}   # (arm, seed) -> list of trials
    for d in sorted(glob.glob(os.path.join(OPTUNA_DIR, "s5-*-seed*"))):
        m = re.search(r"s5-(N|M|A)-seed(\d+)$", d)
        if not m:
            continue
        arm, seed = m.group(1), int(m.group(2))
        csv_path = os.path.join(d, "trials.csv")
        if os.path.exists(csv_path):
            studies[(arm, seed)] = read_study(csv_path)

    if not studies:
        print("未找到 s5-*-seed* 的 trials.csv（扫描可能还在进行）")
        return

    # 全局最优值（用于 target）
    best_global = 0.0
    for trials in studies.values():
        for t in trials:
            best_global = max(best_global, to_float(t.get("value")))
    target = best_global * target_ratio

    rows = []
    for (arm, seed), trials in sorted(studies.items()):
        n = len(trials)
        n_failed = sum(1 for t in trials if (t.get("user_attrs_status") or "ok") != "ok")
        n_violated = sum(1 for t in trials if str(t.get("user_attrs_constraint_violated", "")).lower() == "true")
        # 非法 = 失败 ∪ 违反约束（不能相加，二者重叠）
        n_invalid = sum(
            1 for t in trials
            if ((t.get("user_attrs_status") or "ok") != "ok")
            or str(t.get("user_attrs_constraint_violated", "")).lower() == "true"
        )
        cost = sum(to_float(t.get("user_attrs_experiment_units"), 1.0) for t in trials)
        values = [to_float(t.get("value")) for t in trials]
        best = max(values) if values else 0.0
        ttt = None
        for i, v in enumerate(values):
            if v >= target:
                ttt = i + 1
                break
        rows.append({
            "arm": arm, "seed": seed, "n_trials": n,
            "n_failed": n_failed, "n_constraint_violated": n_violated, "n_invalid": n_invalid,
            "invalid_rate": round(n_invalid / n, 4) if n else 0.0,
            "cumulative_cost": round(cost, 2),
            "best_goodput": round(best, 4),
            "trials_to_target": ttt if ttt is not None else "",
        })

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # 汇总
    def agg(arm, key):
        vals = [r[key] for r in rows if r["arm"] == arm and isinstance(r[key], (int, float))]
        if not vals:
            return "—"
        return f"{statistics.mean(vals):.3f} ± {statistics.stdev(vals):.3f}" if len(vals) > 1 else f"{vals[0]:.3f}"

    def agg_ttt(arm):
        vals = [r["trials_to_target"] for r in rows if r["arm"] == arm and r["trials_to_target"] != ""]
        n_all = len([r for r in rows if r["arm"] == arm])
        if not vals:
            return f"未达标（0/{n_all}）"
        m = statistics.mean(vals)
        s = statistics.stdev(vals) if len(vals) > 1 else 0.0
        return f"{m:.2f} ± {s:.2f}（达标 {len(vals)}/{n_all}）"

    # 空间缩减（离散两维：mns×mtib）
    full = sum(1 for _ in range(1))  # placeholder
    mns_vals = list(range(16, 257))
    mtib_vals = list(range(16, 8193))
    full_pairs = len(mns_vals) * len(mtib_vals)
    legal_pairs = sum(max(0, 8192 - max(m, 1024) + 1) for m in mns_vals)
    reduction = 1 - legal_pairs / full_pairs

    lines = [
        "# S5 汇总（三臂对照）",
        "",
        f"> 数据源：`实验记录/optuna/s5-{{arm}}-seed*/trials.csv` ｜ 目标阈值 = 全局最优 × {target_ratio}（{target:.4f}）",
        "",
        "| 臂 | 累计成本（均值±std） | 非法率 | 最优 goodput | trials-to-target |",
        "|---|---|---|---|---|",
    ]
    for arm, label in (("N", "N 无约束"), ("M", "M 人工约束"), ("A", "A 自动约束")):
        lines.append(f"| {label} | {agg(arm, 'cumulative_cost')} | {agg(arm, 'invalid_rate')} | "
                     f"{agg(arm, 'best_goodput')} | {agg_ttt(arm)} |")

    # 95% CI（bootstrap）
    def vals_of(arm, key):
        return [r[key] for r in rows if r["arm"] == arm and isinstance(r[key], (int, float))]

    def ci_line(arm, key):
        v = vals_of(arm, key)
        if len(v) < 2:
            return "—"
        lo, hi = bootstrap_ci(v)
        return f"{statistics.mean(v):.3f} [{lo:.3f}, {hi:.3f}]"

    lines += ["", "## 95% CI（bootstrap，5000 次重采样）", "",
              "| 臂 | 累计成本 [95% CI] | 非法率 [95% CI] | trials-to-target [95% CI] |",
              "|---|---|---|---|"]
    for arm, label in (("N", "N 无约束"), ("M", "M 人工约束"), ("A", "A 自动约束")):
        ttt_vals = [r["trials_to_target"] for r in rows if r["arm"] == arm and r["trials_to_target"] != ""]
        ttt_txt = "—"
        if len(ttt_vals) >= 2:
            lo, hi = bootstrap_ci(ttt_vals)
            ttt_txt = f"{statistics.mean(ttt_vals):.2f} [{lo:.2f}, {hi:.2f}]"
        lines.append(f"| {label} | {ci_line(arm, 'cumulative_cost')} | {ci_line(arm, 'invalid_rate')} | {ttt_txt} |")

    n_costs = [r["cumulative_cost"] for r in rows if r["arm"] == "N"]
    m_costs = [r["cumulative_cost"] for r in rows if r["arm"] == "M"]
    if len(n_costs) >= 2 and len(m_costs) >= 2:
        mean_red = statistics.mean((a - b) / a for a, b in zip(n_costs, m_costs))
        lo, hi = bootstrap_ci_paired(n_costs, m_costs)
        lines += ["", f"> **成本降低（配对 bootstrap 95% CI）：{mean_red:.1%} [{lo:.1%}, {hi:.1%}]**（n=20 配对种子）"]

    # c_invalid 敏感性：成本(c) = n_trials + n_invalid × c（合法=1，非法=1+c）
    def cost_at(arm, c):
        vals = [r["n_trials"] + r["n_invalid"] * c for r in rows if r["arm"] == arm]
        if not vals:
            return None, None
        return statistics.mean(vals), (statistics.stdev(vals) if len(vals) > 1 else 0.0)

    lines += ["", "## c_invalid 敏感性（成本 = n_trials + n_invalid × c）", "",
              "| 臂 | c=1 | c=3（主口径） | c=10 |", "|---|---|---|---|"]
    for arm, label in (("N", "N 无约束"), ("M", "M 人工约束"), ("A", "A 自动约束")):
        cells = []
        for c in (1, 3, 10):
            m, s = cost_at(arm, c)
            cells.append("—" if m is None else f"{m:.1f} ± {s:.1f}")
        lines.append(f"| {label} | {cells[0]} | {cells[1]} | {cells[2]} |")
    n3, _ = cost_at("N", 3)
    m3, _ = cost_at("M", 3)
    if n3 and m3:
        lines.append("")
        lines.append(f"> c=3 时成本降低 = (N−M)/N = **{(n3 - m3) / n3:.1%}**（G2 判据 >30%）")
    lines += [
        "",
        "## 空间缩减（离散两维 mns×mtib）",
        "",
        f"- 全空间组合数：{full_pairs:,}",
        f"- 约束后合法组合数：{legal_pairs:,}（mtib ≥ max(mns, 1024)）",
        f"- **缩减率：{reduction:.1%}**（真实 vLLM 侧约束覆盖见 `已验证约束.json`：113 条 confirmed = 111 主批次 + 2 跨模型）",
        "",
        f"*生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ 每 seed 明细见 `对比结果.csv`*",
    ]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"studies={len(studies)} rows={len(rows)} target={target:.4f}")
    print(f"-> {OUT_CSV}")
    print(f"-> {OUT_MD}")
    for arm in ("N", "M", "A"):
        sub = [r for r in rows if r["arm"] == arm]
        if sub:
            print(f"  {arm}: cost={agg(arm, 'cumulative_cost')} invalid={agg(arm, 'invalid_rate')} best={agg(arm, 'best_goodput')}")


if __name__ == "__main__":
    main()
