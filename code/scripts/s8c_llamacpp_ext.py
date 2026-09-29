# -*- coding: utf-8 -*-
"""S8c · llama.cpp 真机扩展实验（第二主证据升级版）
- 模型：Qwen2.5-1.5B-Instruct Q4_K_M（若缺失回退 0.5B）
- 空间（216 组合）：threads{2,3,4} × batch{128,256,512} × ubatch{64,128,256} × fa{on,off} × ctk{f16,q8_0} × ctv{f16,q8_0}
- 四臂（trial 级交错）：
    N：无约束
    M：民间规则 ubatch ≤ batch（已证伪，仅此一条）
    A：源码约束（ctv 量化 ⇒ fa=on；n_batch≥1 非绑定）
    S：SCOOT 式 = 民间规则 + 在线学习（首次 q8_0∧fa=off 失败后学会该规则）
- 规模：4 臂 × 5 种子 × 20 trials = 400 次真实推理；每种子后校准
输出：trials-ext.csv / calibration-ext.csv（增量落盘）
"""
import csv
import os
import subprocess
import sys

sys.path.insert(0, "/mnt/f/文献/AgentOps/代码")
import optuna  # noqa: E402

BENCH = "/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench"
MODEL_BIG = os.path.expanduser("~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf")
MODEL_SMALL = os.path.expanduser("~/models/qwen2.5-0.5b-instruct-q4_k_m.gguf")
LIB = os.path.expanduser("~/.venvs/agentops-py311/lib")
OUT_DIR = "/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优"

C_INV = 3.0
N_TRIALS = 20
SEEDS = [1, 2, 3, 4, 5]
THREADS, BATCHES, UBATCHES = [2, 3, 4], [128, 256, 512], [64, 128, 256]
FAS, CTKS, CTVS = ["on", "off"], ["f16", "q8_0"], ["f16", "q8_0"]
CAL_CFG = {"threads": 4, "batch": 256, "ubatch": 128, "fa": "on", "ctk": "f16", "ctv": "f16"}

MODEL = MODEL_BIG if os.path.exists(MODEL_BIG) else MODEL_SMALL
TAG = "1.5b" if MODEL == MODEL_BIG else "0.5b"
OUT_CSV = os.path.join(OUT_DIR, f"trials-ext.csv")
CAL_CSV = os.path.join(OUT_DIR, f"calibration-ext.csv")

if os.environ.get("S8_SMOKE") == "1":
    N_TRIALS = 2
    SEEDS = [99]
    OUT_CSV = os.path.join(OUT_DIR, "trials-ext-smoke.csv")
    CAL_CSV = os.path.join(OUT_DIR, "calibration-ext-smoke.csv")


def run_bench(cfg):
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = f"{LIB}:{env.get('LD_LIBRARY_PATH', '')}"
    cmd = [BENCH, "-m", MODEL, "-t", str(cfg["threads"]), "-b", str(cfg["batch"]),
           "-ub", str(cfg["ubatch"]), "-fa", cfg["fa"], "-ctk", cfg["ctk"], "-ctv", cfg["ctv"],
           "-p", "256", "-n", "16", "-r", "1", "-o", "csv"]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600)
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
        return None, None, "failed", "no pp row"
    return pp, tg, "ok", ""


def q8(cfg):
    # 真机约束只针对 V cache（已实测：ctk=q8_0+fa=off 可运行；ctv=q8_0+fa=off 报错）
    return cfg["ctv"] == "q8_0"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"model={TAG} ({MODEL})", flush=True)
    rows, cals = [], []
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def cal(tag):
        pp, tg, status, err = run_bench(CAL_CFG)
        cals.append({"tag": tag, "pp256": pp, "tg16": tg, "status": status})
        print(f"CAL {tag}: pp={pp}", flush=True)

    cal("start")
    for seed in SEEDS:
        studies = {a: optuna.create_study(direction="maximize",
                                          sampler=optuna.samplers.TPESampler(seed=seed, n_startup_trials=5))
                   for a in ("N", "M", "A", "S")}
        learned = {"S": False}  # S 臂在线学习的规则
        s_first_fail = {"S": None}
        for t in range(N_TRIALS):
            for arm in ("N", "M", "A", "S"):
                tr = studies[arm].ask()
                cfg = {"threads": tr.suggest_categorical("threads", THREADS),
                       "batch": tr.suggest_categorical("batch", BATCHES),
                       "ubatch": tr.suggest_categorical("ubatch", UBATCHES),
                       "fa": tr.suggest_categorical("fa", FAS),
                       "ctk": tr.suggest_categorical("ctk", CTKS),
                       "ctv": tr.suggest_categorical("ctv", CTVS)}
                # M/S：民间规则 ubatch ≤ batch
                if arm in ("M", "S") and cfg["ubatch"] > cfg["batch"]:
                    cfg["ubatch"] = tr.suggest_categorical("ubatch2", [u for u in UBATCHES if u <= cfg["batch"]])
                # A：源码约束（q8 ⇒ fa=on）
                if arm == "A" and q8(cfg):
                    cfg["fa"] = "on"
                # S：在线学习（学会后应用）
                if arm == "S" and learned["S"] and q8(cfg):
                    cfg["fa"] = "on"
                pp, tg, status, err = run_bench(cfg)
                # S：从失败中学习
                if arm == "S" and status != "ok" and q8(cfg) and cfg["fa"] == "off" and not learned["S"]:
                    learned["S"] = True
                    s_first_fail["S"] = t
                    print(f"  [S learns at seed{seed} trial{t}] q8 ⇒ fa=on", flush=True)
                cost = 1.0 if status == "ok" else 1.0 + C_INV
                rows.append({"arm": arm, "seed": seed, "trial": t, **cfg,
                             "pp_256_ts": round(pp, 3) if pp else "", "tg_16_ts": round(tg, 3) if tg else "",
                             "status": status, "cost_units": cost, "error": err, "model": TAG,
                             "s_learned": int(learned["S"]) if arm == "S" else ""})
                studies[arm].tell(tr, pp if pp else 0.0)
                sub = "LEARNED" if (arm == "S" and learned["S"]) else ""
                print(f"{arm} s{seed} t{t:02d} {cfg} -> {status} pp={pp} {sub}", flush=True)
        with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        with open(CAL_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["tag", "pp256", "tg16", "status"])
            w.writeheader()
            w.writerows(cals)
        cal(f"after-seed{seed} ({len(rows)} trials)")
        print(f"seed{seed} done, S first-fail at trial {s_first_fail['S']}", flush=True)
    print("DONE rows:", len(rows))


if __name__ == "__main__":
    main()
