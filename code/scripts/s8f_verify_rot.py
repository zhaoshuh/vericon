# -*- coding: utf-8 -*-
"""S8f · 终验 v2（轮转交错）：每种子内按 N/M/A/S 背靠背复测各臂最佳配置（-r 3）
输出：verification-ext-r3.csv
"""
import csv
import os
import statistics as st
import subprocess

BENCH = "/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench"
LIB = os.path.expanduser("~/.venvs/agentops-py311/lib")
D = "/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优"
MODEL = os.path.expanduser("~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf")

rows = list(csv.DictReader(open(os.path.join(D, "trials-ext.csv"), encoding="utf-8-sig")))
seeds = sorted(set(int(r["seed"]) for r in rows))
arms = ("N", "M", "A", "S")
out = []
for s in seeds:
    for a in arms:  # 轮转：同一种子内四臂背靠背
        sr = [r for r in rows if r["arm"] == a and int(r["seed"]) == s and r["status"] == "ok"]
        best = max(sr, key=lambda r: float(r["pp_256_ts"]))
        cfg = {k: best[k] for k in ("threads", "batch", "ubatch", "fa", "ctk", "ctv")}
        env = dict(os.environ)
        env["LD_LIBRARY_PATH"] = f"{LIB}:{env.get('LD_LIBRARY_PATH', '')}"
        cmd = [BENCH, "-m", MODEL, "-t", cfg["threads"], "-b", cfg["batch"], "-ub", cfg["ubatch"],
               "-fa", cfg["fa"], "-ctk", cfg["ctk"], "-ctv", cfg["ctv"],
               "-p", "256", "-n", "16", "-r", "3", "-o", "csv"]
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
        pp = None
        if r.returncode == 0:
            lines = r.stdout.splitlines()
            cols = None
            for i, line in enumerate(lines):
                if line.startswith("build_commit,"):
                    cols = next(csv.reader([line]))
                    lines = lines[i + 1:]
                    break
            if cols:
                ip, ia = cols.index("n_prompt"), cols.index("avg_ts")
                for line in lines:
                    if line.startswith('"'):
                        parts = next(csv.reader([line]))
                        if parts[ip] == "256":
                            pp = float(parts[ia])
        out.append({"seed": s, "arm": a, **cfg, "pp256_r3": pp, "status": "ok" if pp else "failed"})
        print(f"s{s} {a} {cfg} -> pp(r3)={pp}", flush=True)

with open(os.path.join(D, "verification-ext-r3.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

print("\n| 臂 | 终验(轮转, -r3) 每种子最佳 pp256 | 中位 |")
print("|---|---|---|")
for a in arms:
    v = [x["pp256_r3"] for x in out if x["arm"] == a and x["pp256_r3"]]
    if v:
        print(f"| {a} | {[round(x,1) for x in v]} | {st.median(v):.1f} |")
print("DONE ✓")
