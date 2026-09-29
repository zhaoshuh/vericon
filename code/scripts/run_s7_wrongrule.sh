#!/usr/bin/env bash
# S7 附加轨：把"为 conv 负载校准的阈值（1024）"用到长 prefill 负载 → 展示人工规则的负载不迁移性
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled

MAIN=/mnt/f/文献/AgentOps/实验记录
REC=/tmp/agentops-s7wrong
mkdir -p "$REC"

run_one() {  # tag trace seed
  local tag=$1 trace=$2 s=$3
  local name="s7-$tag-A1024-seed$s"
  echo "[$tag-A1024] s$s $(date +%H:%M:%S)"
  AGENTOPS_RECORDS="$REC" python -m agentops.tune --arm A --seed "$s" --n-trials 30 \
    --space-mode 5d --qps 12.0 --num-requests 384 \
    --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
    --tokens-min 1024 --length-trace "$trace" \
    --study-name "$name" || echo "!! fail $name"
  if [ -d "$REC/optuna/$name" ]; then
    rm -rf "$MAIN/optuna/$name"
    cp -r "$REC/optuna/$name" "$MAIN/optuna/"
  fi
}

for s in 1 2 3 4 5; do
  run_one arxiv arxiv_summarization_stats_llama2_tokenizer_filtered_v2.csv "$s"
done
for s in 1 2 3 4 5; do
  run_one code splitwise_code.csv "$s"
done
echo "S7 WRONG-RULE DONE [$(date +%H:%M:%S)]"
