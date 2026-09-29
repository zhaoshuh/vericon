# -*- coding: utf-8 -*-
"""S8-run2 · 受控复跑：trial 级交错（N/M/A 轮转），模型在 Linux 本地盘，附校准点
- 设计/空间/成本模型与 run1 完全一致（5 种子 × 20 trials × 3 臂 = 300）
- 每种子后跑 1 个固定校准配置（监测环境漂移）
输出：trials-control.csv + calibration.csv
"""
import csv
import os
import subprocess
import sys

sys.path.insert(0, "/mnt/f/文献/AgentOps/代码")
import optuna  # noqa: E402

BENCH = "/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench"
MODEL = os.path.expanduser("~/models/qwen2.5-0.5b-instruct-q4_k_m.gguf")
LIB = os.path.expanduser("~/.venvs/agentops-py311/lib")
OUT_DIR = "/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优"
OUT_CSV = os.path.join(OUT_DIR, "trials-control.csv")
CAL_CSV = os.path.join(OUT_DIR, "calibration.csv")
CAL_CFG = {"threads": 4, "batch": 256, "ubatch": 128, "fa": "on", "ctv": "f16"}

C_INV = 3.0
N_TRIALS = 20
SEEDS = [1, 2, 3, 4, 5]
THREADS, BATCHES, UBATCHES = [2, 3, 4], [128, 256, 512], [64, 128, 256]
FAS, CTVS = ["on", "off"], ["f16", "q8_0"]
if os.environ.get("S8_SMOKE") == "1":
    N_TRIALS = 2
    SEEDS = [99]
    OUT_CSV = os.path.join(OUT_DIR, "trials-control-smoke.csv")
    CAL_CSV = os.path.join(OUT_DIR, "calibration-smoke.csv")


def run_bench(cfg):
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = f"{LIB}:{env.get('LD_LIBRARY_PATH', '')}"
    cmd = [BENCH, "-m", MODEL, "-t", str(cfg["threads"]), "-b", str(cfg["batch"]),
           "-ub", str(cfg["ubatch"]), "-fa", cfg["fa"], "-ctk", "f16", "-ctv", cfg["ctv"],
           "-p", "256", "-n", "16", "-r", "1", "-o", "csv"]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
    except Exception as e:
        return None, None, "timeout", str(e)[:120]
    if r.returncode != 0:
        return None, None, "failed", (r.stderr or r.stdout)[-160:].replace("\n", " ")
    pp = tg = None
    lines = r.stdout.splitlines()
    cols = None
    for i, line in enumerate(lines):
        if line.startswith("build_commit,"):
            cols = next(csv.reader([line]))
            lines = lines[i + 1:]
            break
    if cols is None:
        return None, None, "failed", "no header"
    ip, ig, ia = cols.index("n_prompt"), cols.index("n_gen"), cols.index("avg_ts")
    for line in lines:
        if not line.startswith('"'):
            continue
        parts = next(csv.reader([line]))
        try:
            if parts[ip] == "256":
                pp = float(parts[ia])
            elif parts[ig] == "16":
                tg = float(parts[ia])
        except Exception:
            continue
    if pp is None:
        return None, tg, "failed", "no pp row"
    return pp, tg, "ok", ""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows, cals = [], []
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def cal(tag):
        pp, tg, status, err = run_bench(CAL_CFG)
        cals.append({"tag": tag, "pp256": pp, "tg16": tg, "status": status})
        print(f"CAL {tag}: pp={pp}", flush=True)

    cal("start")
    for si, seed in enumerate(SEEDS):
        studies = {a: optuna.create_study(direction="maximize",
                                          sampler=optuna.samplers.TPESampler(seed=seed, n_startup_trials=5))
                   for a in ("N", "M", "A")}
        for t in range(N_TRIALS):
            for arm in ("N", "M", "A"):  # trial 级交错
                tr = studies[arm].ask()
                cfg = {"threads": tr.suggest_categorical("threads", THREADS),
                       "batch": tr.suggest_categorical("batch", BATCHES),
                       "ubatch": tr.suggest_categorical("ubatch", UBATCHES),
                       "fa": tr.suggest_categorical("fa", FAS),
                       "ctv": tr.suggest_categorical("ctv", CTVS)}
                if arm == "M" and cfg["ubatch"] > cfg["batch"]:
                    cfg["ubatch"] = tr.suggest_categorical("ubatch2", [u for u in UBATCHES if u <= cfg["batch"]])
                if arm == "A" and cfg["ctv"] == "q8_0":
                    cfg["fa"] = "on"
                pp, tg, status, err = run_bench(cfg)
                cost = 1.0 if status == "ok" else 1.0 + C_INV
                rows.append({"arm": arm, "seed": seed, "trial": t, **cfg,
                             "pp_256_ts": round(pp, 3) if pp else "", "tg_16_ts": round(tg, 3) if tg else "",
                             "status": status, "cost_units": cost, "error": err})
                studies[arm].tell(tr, pp if pp else 0.0)
                print(f"{arm} s{seed} t{t:02d} {cfg} -> {status} pp={pp}", flush=True)
        with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        with open(CAL_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["tag", "pp256", "tg16", "status"])
            w.writeheader()
            w.writerows(cals)
        cal(f"after-seed{seed}  ({len(rows)} trials)")
    print("DONE rows:", len(rows))


if __name__ == "__main__":
    main()
