#!/usr/bin/env bash
# 分段计时导入，找出慢在哪
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
export WANDB_MODE=disabled
cd "/mnt/f/文献/AgentOps/代码"
python - <<'PY'
import os, sys, time
os.environ.setdefault("WANDB_MODE", "disabled")
os.environ.setdefault("WANDB_SILENT", "true")

def t(label, fn):
    t0 = time.perf_counter()
    mod = fn()
    print(f"{label:<12} {time.perf_counter()-t0:6.2f}s", flush=True)
    return mod

t("numpy", lambda: __import__("numpy"))
t("pandas", lambda: __import__("pandas"))
t("sklearn", lambda: __import__("sklearn"))
t("plotly_express", lambda: __import__("plotly_express"))
t("wandb", lambda: __import__("wandb"))

from agentops.paths import vidur_dir
sys.path.insert(0, str(vidur_dir()))
t("vidur.config", lambda: __import__("vidur.config", fromlist=["SimulationConfig"]))
t("vidur.simulator", lambda: __import__("vidur.simulator", fromlist=["Simulator"]))
print("ALL_IMPORTS_OK")
PY
