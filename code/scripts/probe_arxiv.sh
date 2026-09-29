#!/usr/bin/env bash
# 探针：arxiv 长 prefill 负载下（arm A，安全下界 4096）的 SLO/goodput 行为
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled
export AGENTOPS_RECORDS=/tmp/agentops-probe
mkdir -p "$AGENTOPS_RECORDS"

python -m agentops.tune --arm A --seed 1 --n-trials 8 --space-mode 5d \
  --qps 12.0 --num-requests 384 --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
  --tokens-min 4096 --length-trace arxiv_summarization_stats_llama2_tokenizer_filtered_v2.csv \
  --study-name probe-arxiv-A 2>&1 | tail -20
