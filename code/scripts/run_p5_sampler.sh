#!/usr/bin/env bash
# P5 采样器在环验证：6d + ConstraintSampler（自动注入），种子 1-3 × 30 trials
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled

GRAPH="/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json,/mnt/f/文献/AgentOps/实验记录/P5-附加约束.json"
for s in 1 2 3; do
  echo "=== p5 sampler 6d arm=A seed=$s [$(date +%H:%M:%S)] ==="
  python -m agentops.tune --arm A --seed "$s" --n-trials 30 --space-mode 6d \
    --qps 12.0 --num-requests 384 --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
    --sampler-graph "$GRAPH" --study-name "p5-6d-graph-A-s$s" || echo "!! fail s$s"
done
echo "P5 SAMPLER RUN DONE"
