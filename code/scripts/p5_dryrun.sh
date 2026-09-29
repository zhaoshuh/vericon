#!/usr/bin/env bash
# P5 采样器 dry-run 冒烟
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
cd /mnt/f/文献/AgentOps/代码
python -m agentops.tune --arm A --seed 1 --n-trials 8 --space-mode 6d \
  --qps 12.0 --num-requests 384 --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
  --sampler-graph "/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json,/mnt/f/文献/AgentOps/实验记录/P5-附加约束.json" \
  --dry-run
