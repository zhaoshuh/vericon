# -*- coding: utf-8 -*-
"""C2 · llama.cpp 真机 A≠M 调优实验（回应审稿人"RQ5 无法识别自动抽取价值"）

三臂：
  N: 无约束
  M: 民间规则（n_ubatch <= n_batch —— 我们已证伪：引擎不强制）
  A: 源码抽取约束（q8_0 V-cache ⇒ flash_attn=on —— 已执行确认）

搜索空间：threads{2,3,4} × batch{128,256,512} × ubatch{64,128,256} × fa{on,off} × ctv{f16,q8_0}（108 组合）
目标：pp256 tok/s（提示处理吞吐，对 batch/ubatch 最敏感）
成本模型：成功=1 单位；失败=1+c（c=3，同 S5 口径）
规模：3 臂 × 5 种子 × 20 trials = 300 次真实推理

输出：实验记录/S8-llamaCpp调优/trials.csv（逐条）+ S8-报告.md
"""
import csv
import os
import subprocess
import sys

sys.path.insert(0, "/mnt/f/文献/AgentOps/代码")
os.environ.setdefault("OMP_NUM_THREADS", "4")

import optuna  # noqa: E402

BENCH = "/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench"
MODEL = "/mnt/f/文献/AgentOps/代码/third_party/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
LIB = os.path.expanduser("~/.venvs/agentops-py311/lib")
OUT_DIR = "/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优"
OUT_CSV = os.path.join(OUT_DIR, "trials.csv")
if os.environ.get("S8_SMOKE") == "1":
    OUT_CSV = os.path.join(OUT_DIR, "trials_smoke.csv")

C_INV = 3.0
N_TRIALS = 20
SEEDS = [1, 2, 3, 4, 5]
# 冒烟模式：S8_SMOKE=1 → 1 臂 × 1 种子 × 2 trials（仅验证解析与失败捕获）
if os.environ.get("S8_SMOKE") == "1":
    N_TRIALS = 2
    SEEDS = [99]

THREADS = [2, 3, 4]
BATCHES = [128, 256, 512]
UBATCHES = [64, 128, 256]
FAS = ["on", "off"]
CTVS = ["f16", "q8_0"]


def run_bench(cfg):
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = f"{LIB}:{env.get('LD_LIBRARY_PATH', '')}"
    cmd = [BENCH, "-m", MODEL,
           "-t", str(cfg["threads"]), "-b", str(cfg["batch"]), "-ub", str(cfg["ubatch"]),
           "-fa", cfg["fa"], "-ctk", "f16", "-ctv", cfg["ctv"],
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
    rows = []
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    for arm in ("N", "M", "A"):
        for seed in SEEDS:
            study = optuna.create_study(direction="maximize",
                                        sampler=optuna.samplers.TPESampler(seed=seed, n_startup_trials=5))
            for t in range(N_TRIALS):
                trial = study.ask()
                cfg = {
                    "threads": trial.suggest_categorical("threads", THREADS),
                    "batch": trial.suggest_categorical("batch", BATCHES),
                    "ubatch": trial.suggest_categorical("ubatch", UBATCHES),
                    "fa": trial.suggest_categorical("fa", FAS),
                    "ctv": trial.suggest_categorical("ctv", CTVS),
                }
                # 约束注入
                if arm == "M" and cfg["ubatch"] > cfg["batch"]:
                    # 民间规则：重新采样至满足 n_ubatch <= n_batch
                    cfg["ubatch"] = trial.suggest_categorical(
                        "ubatch2", [u for u in UBATCHES if u <= cfg["batch"]])
                if arm == "A" and cfg["ctv"] == "q8_0":
                    cfg["fa"] = "on"  # 源码约束：量化 V cache ⇒ flash_attn
                pp, tg, status, err = run_bench(cfg)
                cost = 1.0 if status == "ok" else 1.0 + C_INV
                rows.append({"arm": arm, "seed": seed, "trial": t, **cfg,
                             "pp_256_ts": round(pp, 3) if pp else "",
                             "tg_16_ts": round(tg, 3) if tg else "",
                             "status": status, "cost_units": cost, "error": err})
                study.tell(trial, pp if pp else 0.0)
                print(f"{arm} s{seed} t{t:02d} {cfg} -> {status} pp={pp}", flush=True)

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("DONE ->", OUT_CSV, "rows:", len(rows))


if __name__ == "__main__":
    main()
