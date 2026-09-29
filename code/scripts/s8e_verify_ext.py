# -*- coding: utf-8 -*-
"""S8e · 终验阶段：各臂×种子最佳配置的 5 次重复复测（-r 5）
输出：verification-ext.csv + 终端摘要
"""
import csv
import os
import statistics as st
import subprocess
import sys

sys.path.insert(0, "/mnt/f/文献/AgentOps/代码")

BENCH = "/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench"
LIB = os.path.expanduser("~/.venvs/agentops-py311/lib")
D = "/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优"

rows = list(csv.DictReader(open(os.path.join(D, "trials-ext.csv"), encoding="utf-8-sig")))
MODEL = os.path.expanduser("~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf")
if not os.path.exists(MODEL):
    MODEL = os.path.expanduser("~/models/qwen2.5-0.5b-instruct-q4_k_m.gguf")

seeds = sorted(set(int(r["seed"]) for r in rows))
arms = ("N", "M", "A", "S")
out = []
for a in arms:
    for s in seeds:
        sr = [r for r in rows if r["arm"] == a and int(r["seed"]) == s and r["status"] == "ok"]
        if not sr:
            continue
        best = max(sr, key=lambda r: float(r["pp_256_ts"]))
        cfg = {k: best[k] for k in ("threads", "batch", "ubatch", "fa", "ctk", "ctv")}
        env = dict(os.environ)
        env["LD_LIBRARY_PATH"] = f"{LIB}:{env.get('LD_LIBRARY_PATH', '')}"
        cmd = [BENCH, "-m", MODEL, "-t", cfg["threads"], "-b", cfg["batch"], "-ub", cfg["ubatch"],
               "-fa", cfg["fa"], "-ctk", cfg["ctk"], "-ctv", cfg["ctv"],
               "-p", "256", "-n", "16", "-r", "5", "-o", "csv"]
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
        pp = tg = None
        if r.returncode == 0:
            lines = r.stdout.splitlines()
            cols = None
            for i, line in enumerate(lines):
                if line.startswith("build_commit,"):
                    cols = next(csv.reader([line]))
                    lines = lines[i + 1:]
                    break
            if cols:
                ip, ig, ia = cols.index("n_prompt"), cols.index("n_gen"), cols.index("avg_ts")
                for line in lines:
                    if not line.startswith('"'):
                        continue
                    parts = next(csv.reader([line]))
                    if parts[ip] == "256":
                        pp = float(parts[ia])
                    elif parts[ig] == "16":
                        tg = float(parts[ia])
        out.append({"arm": a, "seed": s, **cfg, "pp256_r5": pp, "tg16_r5": tg,
                    "status": "ok" if pp else "failed"})
        print(f"{a} s{s} {cfg} -> pp(r5)={pp}", flush=True)

with open(os.path.join(D, "verification-ext.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

print("\n| 臂 | 终验 pp256（中位，-r5）|")
print("|---|---|")
for a in arms:
    v = [x["pp256_r5"] for x in out if x["arm"] == a and x["pp256_r5"]]
    if v:
        print(f"| {a} | {st.median(v):.1f} |")
print("DONE -> verification-ext.csv")
