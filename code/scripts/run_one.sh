#!/usr/bin/env bash
# 跑一条配置（WSL）。用法示例：
#   bash scripts/run_one.sh --max-num-seqs 64 --max-num-batched-tokens 2048
set -euo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
# WSL 本地快照可显著加快 Vidur 导入（见 scripts/setup_env_miniconda.sh）
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd "/mnt/f/文献/AgentOps/代码"
export WANDB_MODE=disabled
exec python -m agentops.run_one "$@"
