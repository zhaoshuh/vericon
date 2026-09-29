# -*- coding: utf-8 -*-
"""重生成 Fig. 2：全部 716 条约束的类型分布，按 tier 堆叠（core 282 + extension 434）"""
import json
import os
import shutil
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/mnt/f/文献/AgentOps"
FIG_SRC = os.path.join(ROOT, "论文", "figs")
FIG_LATEX = os.path.join(ROOT, "论文", "latex", "figs")

plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "figure.dpi": 200})

old = json.load(open(f"{ROOT}/实验记录/约束图.json", encoding="utf-8"))
new = json.load(open(f"{ROOT}/实验记录/约束图-v1-ext.json", encoding="utf-8"))
c_old = Counter(n["type"] for n in old["nodes"])
c_new = Counter(n["type"] for n in new["nodes"])
ext = {k: c_new[k] - c_old.get(k, 0) for k in c_new}
assert sum(c_old.values()) == 282, sum(c_old.values())
assert sum(c_new.values()) == 716, sum(c_new.values())
assert sum(ext.values()) == 434 and all(v >= 0 for v in ext.values()), ext

items = sorted(c_new.items(), key=lambda kv: -kv[1])
labels = [k for k, _ in items]
core = [c_old[k] for k, _ in items]
exts = [ext[k] for k, _ in items]
tot = [c_new[k] for k, _ in items]
print("labels:", labels)
print("core  :", core)
print("ext   :", exts)
print("totals:", tot)

fig, ax = plt.subplots(figsize=(4.2, 2.55))
ax.bar(labels, core, color="#4c72b0", label="core tiers (282)")
ax.bar(labels, exts, bottom=core, color="#a6c8e0", label="full-coverage extension (434)")
for i, tv in enumerate(tot):
    ax.text(i, tv + 7, str(tv), ha="center", fontsize=7.5)
ax.set_ylabel("# constraints")
ax.set_title("Constraint types (716 total: 282 core + 434 extension)")
ax.tick_params(axis="x", rotation=38, labelsize=7)
for t in ax.get_xticklabels():
    t.set_ha("right")
ax.set_ylim(0, 350)
ax.legend(fontsize=7, frameon=False, loc="upper right")
fig.tight_layout()

for d in (FIG_SRC, FIG_LATEX):
    fig.savefig(os.path.join(d, "fig2_types.png"), bbox_inches="tight")
    fig.savefig(os.path.join(d, "fig2_types.pdf"), bbox_inches="tight")
plt.close(fig)
print("fig2 regenerated -> both figs dirs")
