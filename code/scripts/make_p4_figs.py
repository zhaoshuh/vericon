# -*- coding: utf-8 -*-
"""生成 P4/P5 图表 → 论文/figs/fig8_dimension_curve.* 与 fig9_sampler_analysis.*
数据：实验记录/P4-结果.csv（analyze_p4.py 产物）
运行（WSL）：bash run_make_p4_figs.sh
"""
import csv
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/mnt/f/文献/AgentOps"
FIGS = os.path.join(ROOT, "论文", "figs")
P4CSV = os.path.join(ROOT, "实验记录", "P4-结果.csv")
os.makedirs(FIGS, exist_ok=True)

C_N, C_M, C_A = "#d62728", "#1f77b4", "#2ca02c"
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 200})
SEEDS = set(range(1, 11))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, name + ".png"), bbox_inches="tight")
    fig.savefig(os.path.join(FIGS, name + ".pdf"), bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def load():
    rows = []
    with open(P4CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            try:
                r["seed"] = int(r["seed"])
                r["qps"] = float(r["qps"])
                r["cumulative_cost"] = float(r["cumulative_cost"])
                r["invalid_rate"] = float(r["invalid_rate"])
            except Exception:
                continue
            rows.append(r)
    return rows


def agg(rows, mode, qps, arm):
    v = [r["cumulative_cost"] for r in rows
         if r["mode"] == mode and abs(r["qps"] - qps) < 1e-9 and r["arm"] == arm and r["seed"] in SEEDS]
    if not v:
        return None, None
    return statistics.mean(v), (statistics.stdev(v) if len(v) > 1 else 0.0)


def fig8(rows):
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.8))
    # Panel A: dimension curve at qps=12
    modes = ["2d", "5d", "6d"]
    ax = axes[0]
    w = 0.26
    xs = range(len(modes))
    for k, (arm, col, lab) in enumerate((("N", C_N, "N unconstrained"), ("M", C_M, "M manual"), ("A", C_A, "A automatic"))):
        means, errs = [], []
        for m in modes:
            mu, sd = agg(rows, m, 12.0, arm)
            means.append(mu or 0)
            errs.append(sd or 0)
        ax.bar([x + (k - 1) * w for x in xs], means, width=w, yerr=errs, capsize=2, color=col, label=lab)
    for i, m in enumerate(modes):
        muN, _ = agg(rows, m, 12.0, "N")
        muA, _ = agg(rows, m, 12.0, "A")
        if muN and muA:
            ax.text(i, (muN or 0) * 1.02, f"−{(muN - muA) / muN:.0%}", ha="center", fontsize=8, color="#333")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{m}\n(seeds 1–10)" for m in modes])
    ax.set_ylabel("cumulative cost (units)")
    ax.set_title("(a) Dimension scaling (qps = 12)")
    ax.legend(fontsize=6.5, frameon=False, loc="upper center", ncol=3, columnspacing=1.0)
    ax.set_ylim(0, 98)
    # Panel B: workload robustness at 5d
    qs = [8.0, 12.0, 16.0]
    ax = axes[1]
    xs = range(len(qs))
    for k, (arm, col, lab) in enumerate((("N", C_N, "N"), ("M", C_M, "M"), ("A", C_A, "A"))):
        means, errs = [], []
        for q in qs:
            mu, sd = agg(rows, "5d", q, arm)
            means.append(mu or 0)
            errs.append(sd or 0)
        ax.bar([x + (k - 1) * w for x in xs], means, width=w, yerr=errs, capsize=2, color=col, label=lab)
    for i, q in enumerate(qs):
        muN, _ = agg(rows, "5d", q, "N")
        muA, _ = agg(rows, "5d", q, "A")
        if muN and muA:
            ax.text(i, (muN or 0) * 1.02, f"−{(muN - muA) / muN:.0%}", ha="center", fontsize=8, color="#333")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"qps={q:g}" for q in qs])
    ax.set_ylabel("cumulative cost (units)")
    ax.set_title("(b) Workload robustness (5d)")
    ax.legend(fontsize=6.5, frameon=False, loc="upper center", ncol=3, columnspacing=1.0)
    ax.set_ylim(0, 98)
    save(fig, "fig8_dimension_curve")


def fig9():
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.8))
    # Panel A: violation rates under different sampling regimes
    ax = axes[0]
    names = ["nominal\ngrid", "log-uniform\n(analytic)", "TPE\n(measured)", "constrained\nsampler"]
    vals = [12.3, 83.3, 31.5, 0.0]
    cols = ["#999999", "#d62728", "#ff9f43", "#2ca02c"]
    ax.bar(range(4), vals, color=cols, width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.5, f"{v:.1f}%", ha="center", fontsize=8)
    ax.set_xticks(range(4))
    ax.set_xticklabels(names, fontsize=7)
    ax.set_ylabel("violation rate (%)")
    ax.set_ylim(0, 95)
    ax.set_title("(a) Waste depends on the sampling distribution")
    # Panel B: analytic savings curve + measured point
    ax = axes[1]
    rs = [i / 100 for i in range(1, 100)]
    for c, col in ((1, "#8c8c8c"), (3, "#1f77b4"), (10, "#2ca02c")):
        ys = [c * r / (1 + c * r) for r in rs]
        ax.plot(rs, ys, color=col, lw=1.4, label=f"$c_{{invalid}}$ = {c}")
    ax.axhline(0.30, color="#d62728", ls="--", lw=0.9)
    ax.text(0.02, 0.315, "30% gate", color="#d62728", fontsize=7)
    # measured point (TPE r_b=31.5%, c=3)
    ax.scatter([0.315], [0.486], color="#d62728", zorder=5, s=22)
    ax.annotate("measured: 31.5% → 48.6%", (0.315, 0.486), textcoords="offset points",
                xytext=(8, -12), fontsize=7, color="#d62728")
    ax.set_xlabel("$r_{before}$ (invalid rate, unconstrained)")
    ax.set_ylabel("cost saving")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7, frameon=False, loc="lower right")
    ax.set_title("(b) Analytical relation (verified vs measured)")
    save(fig, "fig9_sampler_analysis")


def main():
    rows = load()
    if not rows:
        print("no P4 data yet")
        return
    fig8(rows)
    fig9()
    print("done")


if __name__ == "__main__":
    main()
