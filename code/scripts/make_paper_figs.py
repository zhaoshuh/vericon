# -*- coding: utf-8 -*-
"""生成 Paper 1 图表（全部数据来自 实验记录/）→ 论文/figs/*.png|pdf

运行（WSL）：bash run_make_figs.sh
"""
import csv
import glob
import json
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = "/mnt/f/文献/AgentOps"
FIGS = os.path.join(ROOT, "论文", "figs")
os.makedirs(FIGS, exist_ok=True)

C_N, C_M, C_A = "#d62728", "#1f77b4", "#2ca02c"
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 200})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, name + ".png"), bbox_inches="tight")
    fig.savefig(os.path.join(FIGS, name + ".pdf"), bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


# ---------- Fig 1: pipeline ----------
def fig_pipeline():
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    ax.axis("off")
    boxes_top = [
        (0.02, "Engine source\n(vLLM v0.30.0, llama.cpp)"),
        (0.27, "AST inventory\n9,670 fields / 262 CLI flags"),
        (0.52, "Candidate scan\n13,301 validation sites"),
        (0.77, "Agent structuring\n282 constraints (file:line)"),
    ]
    boxes_bottom = [
        (0.77, "Falsification\n155 cases executed"),
        (0.52, "Verified set\n113 confirmed"),
        (0.27, "Tuner injection\nOptuna sampling bounds"),
        (0.02, "Measured benefit\ncost −48.6%"),
    ]
    w, h = 0.21, 0.26
    for x, label in boxes_top:
        ax.add_patch(FancyBboxPatch((x, 0.62), w, h, boxstyle="round,pad=0.012",
                                    fc="#eef4fb", ec="#33608c", lw=1.0))
        ax.text(x + w / 2, 0.75, label, ha="center", va="center", fontsize=8)
    for x, label in boxes_bottom:
        ax.add_patch(FancyBboxPatch((x, 0.12), w, h, boxstyle="round,pad=0.012",
                                    fc="#eef7ee", ec="#3a7d3a", lw=1.0))
        ax.text(x + w / 2, 0.25, label, ha="center", va="center", fontsize=8)
    for i in range(3):
        ax.add_patch(FancyArrowPatch((0.02 + i * 0.25 + w, 0.75), (0.27 + i * 0.25, 0.75),
                                     arrowstyle="->", mutation_scale=12, color="#444"))
    # down from last top to first bottom
    ax.add_patch(FancyArrowPatch((0.875, 0.62), (0.875, 0.38), arrowstyle="->",
                                 mutation_scale=12, color="#444"))
    for i in range(3):
        ax.add_patch(FancyArrowPatch((0.77 - i * 0.25, 0.25), (0.52 - i * 0.25 + w, 0.25),
                                     arrowstyle="->", mutation_scale=12, color="#444"))
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0.05, 0.95)
    ax.set_title("Extract–Falsify–Inject pipeline", pad=4)
    save(fig, "fig1_pipeline")


# ---------- Fig 2: constraint type distribution ----------
def fig_types():
    g = json.load(open(os.path.join(ROOT, "实验记录", "约束图.json"), encoding="utf-8"))
    from collections import Counter
    c = Counter(n["type"] for n in g["nodes"])
    items = sorted(c.items(), key=lambda kv: -kv[1])
    fig, ax = plt.subplots(figsize=(4.2, 2.4))
    ax.bar([k for k, _ in items], [v for _, v in items], color="#4c72b0")
    for i, (k, v) in enumerate(items):
        ax.text(i, v + 1.5, str(v), ha="center", fontsize=8)
    ax.set_ylabel("# constraints")
    ax.set_title("Extracted constraint types (282 total)")
    ax.tick_params(axis="x", rotation=40, labelsize=7)
    for t in ax.get_xticklabels():
        t.set_ha("right")
    save(fig, "fig2_types")


# ---------- Fig 6: validation status ----------
def fig_status():
    g = json.load(open(os.path.join(ROOT, "实验记录", "约束图.json"), encoding="utf-8"))
    from collections import Counter
    c = Counter((n.get("validation") or {}).get("status", "not_tested") for n in g["nodes"])
    order = ["confirmed", "no_error", "blocked", "not_tested"]
    vals = [c.get(k, 0) for k in order]
    colors = ["#2ca02c", "#ff7f0e", "#d62728", "#bbbbbb"]
    fig, ax = plt.subplots(figsize=(4.2, 2.2))
    bars = ax.bar(order, vals, color=colors)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 3, str(v), ha="center", fontsize=8)
    ax.set_ylabel("# constraints")
    ax.set_title("Execution-based falsification status (vLLM v0.30.0)")
    save(fig, "fig6_status")


# ---------- S5 data ----------
def load_studies():
    out = {"N": [], "M": [], "A": []}
    for arm in out:
        for d in sorted(glob.glob(os.path.join(ROOT, "实验记录", "optuna", f"s5-{arm}-seed*"))):
            p = os.path.join(d, "trials.csv")
            if not os.path.exists(p):
                continue
            rows = []
            with open(p, encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    rows.append(r)
            out[arm].append(rows)
    return out


def _f(row, key, default=0.0):
    try:
        return float(row.get(key) or default)
    except Exception:
        return default


def fig_cost_curves(studies):
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    styles = {"N": dict(color=C_N, lw=1.6, ls="-"),
              "M": dict(color=C_M, lw=2.2, ls="--"),
              "A": dict(color=C_A, lw=1.4, ls="-")}
    for arm in ("N", "M", "A"):
        curves = []
        for rows in studies[arm]:
            cum, acc = [], 0.0
            for r in rows:
                acc += _f(r, "user_attrs_experiment_units", 1.0)
                cum.append(acc)
            curves.append(cum)
        n = min(len(c) for c in curves)
        mean = [statistics.mean(c[i] for c in curves) for i in range(n)]
        std = [statistics.pstdev(c[i] for c in curves) for i in range(n)]
        x = list(range(1, n + 1))
        ax.plot(x, mean, label=f"{arm}", **styles[arm])
        ax.fill_between(x, [m - s for m, s in zip(mean, std)],
                        [m + s for m, s in zip(mean, std)], color=styles[arm]["color"], alpha=0.15)
    ax.text(0.98, 0.02, "M and A coincide by construction", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7, color="#555")
    ax.set_xlabel("trial")
    ax.set_ylabel("cumulative cost (units)")
    ax.set_title("Cumulative tuning cost (20 seeds, mean ± std)")
    ax.legend()
    save(fig, "fig3_cost_curves")


def fig_convergence(studies):
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    styles = {"N": dict(color=C_N, lw=1.6, ls="-"),
              "M": dict(color=C_M, lw=2.2, ls="--"),
              "A": dict(color=C_A, lw=1.4, ls="-")}
    for arm in ("N", "M", "A"):
        curves = []
        for rows in studies[arm]:
            best, cum = [], 0.0
            for r in rows:
                cum = max(cum, _f(r, "value"))
                best.append(cum)
            curves.append(best)
        n = min(len(c) for c in curves)
        mean = [statistics.mean(c[i] for c in curves) for i in range(n)]
        std = [statistics.pstdev(c[i] for c in curves) for i in range(n)]
        x = list(range(1, n + 1))
        ax.plot(x, mean, label=f"{arm}", **styles[arm])
        ax.fill_between(x, [m - s for m, s in zip(mean, std)],
                        [m + s for m, s in zip(mean, std)], color=styles[arm]["color"], alpha=0.15)
    ax.text(0.98, 0.02, "M and A coincide by construction", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7, color="#555")
    ax.set_xlabel("trial")
    ax.set_ylabel("best goodput so far (req/s)")
    ax.set_title("Best-so-far goodput (20 seeds, mean ± std)")
    ax.legend()
    save(fig, "fig4_convergence")


def fig_cost_box():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "实验记录", "对比结果.csv"),
                                    encoding="utf-8-sig")))
    data = {arm: [float(r["cumulative_cost"]) for r in rows if r["arm"] == arm] for arm in "NMA"}
    fig, ax = plt.subplots(figsize=(3.6, 2.6))
    bp = ax.boxplot([data["N"], data["M"], data["A"]], tick_labels=["N", "M", "A"], patch_artist=True)
    for patch, color in zip(bp["boxes"], [C_N, C_M, C_A]):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
    ax.set_ylabel("total cost per seed (units)")
    ax.set_title("Cost distribution (20 seeds/arm)")
    save(fig, "fig5_cost_box")


def fig7_type_status():
    g = json.load(open(os.path.join(ROOT, "实验记录", "约束图.json"), encoding="utf-8"))
    from collections import defaultdict
    types = ["implication", "mutual_exclusion", "range", "arithmetic", "enum", "inequality", "type"]
    statuses = ["confirmed", "no_error", "blocked", "not_tested"]
    colors = {"confirmed": "#2ca02c", "no_error": "#ff7f0e", "blocked": "#d62728", "not_tested": "#bbbbbb"}
    data = defaultdict(lambda: defaultdict(int))
    for n in g["nodes"]:
        st = (n.get("validation") or {}).get("status", "not_tested")
        data[n["type"]][st] += 1
    fig, ax = plt.subplots(figsize=(5.0, 2.6))
    bottom = [0] * len(types)
    for st in statuses:
        vals = [data[t].get(st, 0) for t in types]
        ax.bar(types, vals, bottom=bottom, label=st, color=colors[st])
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_ylabel("# constraints")
    ax.set_title("Constraint types × falsification status")
    ax.tick_params(axis="x", rotation=40, labelsize=7)
    for t in ax.get_xticklabels():
        t.set_ha("right")
    ax.legend(fontsize=7)
    save(fig, "fig7_type_status")


def main():
    fig_pipeline()
    fig_types()
    fig_status()
    fig7_type_status()
    studies = load_studies()
    if studies["N"]:
        fig_cost_curves(studies)
        fig_convergence(studies)
        fig_cost_box()
    print("ALL FIGS DONE ->", FIGS)


if __name__ == "__main__":
    main()
