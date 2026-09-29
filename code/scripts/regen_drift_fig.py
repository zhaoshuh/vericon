# -*- coding: utf-8 -*-
"""新图 v2：SCOOT 三规则 × 六个 vLLM 版本的生命周期（修正图例/标注/标签）"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = "/mnt/f/文献/AgentOps"
FIG_SRC = os.path.join(ROOT, "论文", "figs")
FIG_LATEX = os.path.join(ROOT, "论文", "latex", "figs")

plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9.5, "figure.dpi": 200})

versions = ["v0.4.2", "v0.5.5", "v0.6.6", "v0.8.0", "v0.10.0", "v0.30.0"]
x = list(range(len(versions)))
exec_tested = [False, True, False, False, True, True]

rows = [
    ("R1  mtib \u2265 mns", [2, 2, 2, 2, 2, 2]),
    ("R2  chunked \u22a5 prefix", [2, 2, 0, 0, 0, 0]),
    ("R3  mtib \u2265 max_model_len", [2, 2, 2, 2, 2, 1]),
]

GREEN, ORANGE, RED = "#2ca02c", "#dd8452", "#d62728"

fig, ax = plt.subplots(figsize=(4.3, 2.5))
for yi, (label, states) in enumerate(reversed(rows)):
    y = [yi] * len(x)
    ax.plot(x, y, "-", color="#bbbbbb", lw=0.8, zorder=1)
    for xi, st in zip(x, states):
        if st == 2:
            ax.plot(xi, yi, marker="o", ms=8, mfc=GREEN, mec=GREEN, zorder=3)
        elif st == 1:
            ax.plot(xi, yi, marker="o", ms=8, fillstyle="left", mfc=ORANGE, mec=ORANGE, zorder=3)
        else:
            ax.plot(xi, yi, marker="o", ms=8, mfc="white", mec=RED, mew=1.6, zorder=3)

ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=8)
for xi, t in zip(x, exec_tested):
    if t:
        ax.plot(xi, -0.80, marker="^", ms=6, color="#1f77b4", zorder=3)
ax.set_ylim(-1.12, 2.55)
ax.set_xlim(-0.5, len(x) - 0.5)
ax.set_xticks(x)
ax.set_xticklabels(versions, fontsize=7.5, rotation=18, ha="right")

ax.annotate("guard removed\n(v0.6.6+)", xy=(2.05, 0.95), xytext=(2.48, 0.42),
            fontsize=6.8, color=RED, ha="left", va="center",
            arrowprops=dict(arrowstyle="->", color=RED, lw=0.8))
ax.annotate("practical force lost (V1 defaults)", xy=(5.0, 0.0), xytext=(2.4, -0.45),
            fontsize=6.6, color=ORANGE, ha="left", va="center",
            arrowprops=dict(arrowstyle="->", color=ORANGE, lw=0.8))

handles = [
    Line2D([], [], marker="o", ls="", ms=7, mfc=GREEN, mec=GREEN, label="enforced / stable"),
    Line2D([], [], marker="o", ls="", ms=7, fillstyle="left", mfc=ORANGE, mec=ORANGE, label="weakened by defaults"),
    Line2D([], [], marker="o", ls="", ms=7, mfc="white", mec=RED, mew=1.6, label="removed / absent"),
    Line2D([], [], marker="^", ls="", ms=6, color="#1f77b4", label="execution-tested"),
]
ax.legend(handles=handles, fontsize=6.6, ncol=2, frameon=False, loc="lower left",
          bbox_to_anchor=(0.02, 1.0), borderaxespad=0.0, handletextpad=0.4, columnspacing=1.2)
ax.set_title("SCOOT's three hand-written rules across six vLLM releases", pad=26)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()

for d in (FIG_SRC, FIG_LATEX):
    fig.savefig(os.path.join(d, "fig_drift_rules.png"), bbox_inches="tight")
    fig.savefig(os.path.join(d, "fig_drift_rules.pdf"), bbox_inches="tight")
plt.close(fig)
print("saved fig_drift_rules v2")
