#!/usr/bin/env bash
# 量化：把 vidur 包放到 WSL 原生盘后，导入能快多少
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
export WANDB_MODE=disabled
REPO="/mnt/f/文献/AgentOps/代码/third_party/vidur"
FAST="$HOME/vidur-fast"

echo "--- 准备 WSL 本地副本（只复制代码包，data 用软链接） ---"
mkdir -p "$FAST"
cp -r "$REPO/vidur" "$FAST/" 2>/dev/null
ln -sfn "$REPO/data" "$FAST/data"
ls "$FAST" | head

echo "--- 计时：本地副本导入 ---"
export FAST="$FAST"
python - <<'PY'
import os, sys, time
sys.path.insert(0, os.environ["FAST"])
t0 = time.perf_counter()
from vidur.simulator import Simulator
print(f"vidur.simulator 导入耗时: {time.perf_counter()-t0:.2f}s")
PY
