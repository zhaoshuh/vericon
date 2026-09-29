# -*- coding: utf-8 -*-
"""S7 负载迁移分析：arxiv（长 prefill）与 code（超长 prefill）上的 N/S/M/A 对照
输出：实验记录/S7-结果.csv、S7-报告.md
"""
import csv
import glob
import os
import re
import statistics
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OPT = r"F:\文献\AgentOps\实验记录\optuna"
OUT_CSV = r"F:\文献\AgentOps\实验记录\S7-结果.csv"
OUT_MD = r"F:\文献\AgentOps\实验记录\S7-报告.md"


def read_study(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def boot_paired(a, b, n_boot=5000, alpha=0.05, seed=42):
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
    for d in sorted(glob.glob(os.path.join(OPT, "s7-*-seed*"))):
        base = os.path.basename(d)
        m = re.match(r"s7-(arxiv|code)-(N|S|M|A)-seed(\d+)$", base)
        if m:
            csv_path = os.path.join(d, "trials.csv")
            if os.path.exists(csv_path):
                studies[(m.group(1), m.group(2), int(m.group(3)))] = read_study(csv_path)
        else:
            m2 = re.match(r"s7-(arxiv|code)-A1024-seed(\d+)$", base)
            if m2:
                csv_path = os.path.join(d, "trials.csv")
                if os.path.exists(csv_path):
                    studies[(m2.group(1), "A1024", int(m2.group(2)))] = read_study(csv_path)

    rows = []
    for (tag, arm, seed), trials in sorted(studies.items()):
        n = len(trials)
        n_invalid = sum(
            1 for t in trials
            if ((t.get("user_attrs_status") or "ok") != "ok")
            or str(t.get("user_attrs_constraint_violated", "")).lower() == "true"
        )
        cost = sum(to_float(t.get("user_attrs_experiment_units"), 1.0) for t in trials)
        values = [to_float(t.get("value")) for t in trials]
        best = max(values) if values else 0.0
        rows.append({"trace": tag, "arm": arm, "seed": seed, "n": n,
                     "n_invalid": n_invalid,
                     "invalid_rate": round(n_invalid / n, 4) if n else 0.0,
                     "cumulative_cost": round(cost, 2), "best_goodput": round(best, 4)})

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def vals(tag, arm, key):
        return [r[key] for r in rows if r["trace"] == tag and r["arm"] == arm and isinstance(r[key], (int, float))]

    def agg(tag, arm, key):
        v = vals(tag, arm, key)
        return f"{statistics.mean(v):.2f} ± {statistics.stdev(v):.2f}" if len(v) > 1 else (f"{v[0]:.2f}" if v else "—")

    def paired(tag, a, b, key="cumulative_cost"):
        va = {r["seed"]: r[key] for r in rows if r["trace"] == tag and r["arm"] == a}
        vb = {r["seed"]: r[key] for r in rows if r["trace"] == tag and r["arm"] == b}
        common = sorted(set(va) & set(vb))
        if len(common) < 2:
            return "—"
        xa = [va[s] for s in common]
        xb = [vb[s] for s in common]
        mean = statistics.mean((x - y) / x for x, y in zip(xa, xb))
        lo, hi = boot_paired(xa, xb)
        return f"{mean:.1%} [{lo:.1%}, {hi:.1%}]（n={len(common)}）"

    md = [
        "# S7 · 负载迁移报告（长 prefill 工作负载）",
        "",
        "> 三条负载：`splitwise_conv`（会话，p50≈1.0K prefill）/ `arxiv`（摘要，p50≈2.7K）/ `splitwise_code`（代码，p90≈5.2K）；",
        "> 协议：5d @ qps=12，10 种子 × 30 trials，**统一阈值 tokens_min=1024**（失败分布证实：三条 trace 的失败全在 mtib ≤ 1008、成功最小 ≥ 1025 → 阈值 trace 无关）；",
        "> A1024 对照 = 仅改阈值的同构臂（验证阈值选择不影响结论）。",
        "",
    ]
    for tag, tmin, desc in (("arxiv", 4096, "长 prefill（摘要）"), ("code", 7500, "超长 prefill（代码）")):
        md += [f"## {tag}（{desc}）", "",
               "| 臂 | 累计成本 | 非法率 | 最优 goodput |", "|---|---|---|---|"]
        for arm, lab in (("N", "N 无约束"), ("S", "S 在线学习"), ("M", "M 人工约束"), ("A", "A 自动约束"), ("A1024", "A（统一阈值 1024，对照）")):
            if vals(tag, arm, "cumulative_cost"):
                md.append(f"| {lab} | {agg(tag, arm, 'cumulative_cost')} | {agg(tag, arm, 'invalid_rate')} | {agg(tag, arm, 'best_goodput')} |")
        md += ["", "**配对降低**：",
               f"- N → M/A：{paired(tag, 'N', 'A')}",
               f"- N → S：{paired(tag, 'N', 'S')}",
               f"- S → A：{paired(tag, 'S', 'A')}", ""]
    md += ["*生成：2026-09-28 ｜ 明细见 `S7-结果.csv`*"]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))

    print(f"studies={len(rows)}")
    for tag in ("arxiv", "code"):
        for arm in ("N", "S", "M", "A"):
            if vals(tag, arm, "cumulative_cost"):
                print(f"  {tag}/{arm}: cost={agg(tag, arm, 'cumulative_cost')} invalid={agg(tag, arm, 'invalid_rate')}")
        print(f"  {tag}: N->A={paired(tag, 'N', 'A')} | S->A={paired(tag, 'S', 'A')}")
    print("->", OUT_MD)


if __name__ == "__main__":
    main()
