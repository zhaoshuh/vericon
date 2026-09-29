# -*- coding: utf-8 -*-
"""S6 · Phase B：llama.cpp 真实性能网格（llama-bench JSON → CSV）

运行（WSL）：见 run_s6_bench.sh
产出：实验记录/llamacpp_anchor.csv
"""
import csv
import json
import os
import subprocess
import sys
import time

BIN = "/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194"
MODEL = "/mnt/f/文献/AgentOps/代码/third_party/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
OUT = "/mnt/f/文献/AgentOps/实验记录/llamacpp_anchor.csv"
ENV = dict(os.environ)
ENV["LD_LIBRARY_PATH"] = os.path.expanduser("~/.venvs/agentops-py311/lib") + ":" + ENV.get("LD_LIBRARY_PATH", "")

# 网格：threads × n_batch × n_ubatch（受 n_ubatch <= n_batch 约束）
CONFIGS = [(t, b, ub)
           for t in (2, 3, 4)
           for b in (128, 256, 512)
           for ub in (64, 128, 256)
           if ub <= b]


def run_bench(t, b, ub, reps=2):
    cmd = [f"{BIN}/llama-bench", "-m", MODEL,
           "-p", "512", "-n", "64",
           "-t", str(t), "-b", str(b), "-ub", str(ub),
           "-r", str(reps), "-o", "json"]
    t0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=ENV)
        wall = round(time.perf_counter() - t0, 2)
        if p.returncode != 0:
            return {"pp512_tps": None, "tg64_tps": None, "wall_s": wall,
                    "status": "failed", "error": (p.stderr or "")[-300:]}
        data = json.loads(p.stdout)
        pp = next((x for x in data if x.get("n_prompt")), None)
        tg = next((x for x in data if x.get("n_gen")), None)
        return {"pp512_tps": round(pp["avg_ts"], 2) if pp else None,
                "tg64_tps": round(tg["avg_ts"], 2) if tg else None,
                "wall_s": wall, "status": "ok", "error": ""}
    except Exception as e:
        return {"pp512_tps": None, "tg64_tps": None,
                "wall_s": round(time.perf_counter() - t0, 2),
                "status": "failed", "error": f"{type(e).__name__}: {e}"[:300]}


def main():
    if not os.path.exists(MODEL):
        print(f"模型不存在: {MODEL}（等待下载完成）")
        return
    reps, out = 2, OUT
    args = sys.argv[1:]
    if "--reps" in args:
        reps = int(args[args.index("--reps") + 1])
    if "--out" in args:
        out = args[args.index("--out") + 1]
    rows = []
    for (t, b, ub) in CONFIGS:
        r = run_bench(t, b, ub, reps=reps)
        row = {"threads": t, "n_batch": b, "n_ubatch": ub, "reps": reps, **r}
        rows.append(row)
        print(f"t={t} b={b} ub={ub} -> {r['status']:6s} pp512={r['pp512_tps']} tg64={r['tg64_tps']} wall={r['wall_s']}s")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"-> {out}  ({len(rows)} configs, reps={reps})")


if __name__ == "__main__":
    main()
