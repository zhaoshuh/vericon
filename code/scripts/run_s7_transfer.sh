#!/usr/bin/env bash
# S7 负载迁移：arxiv（长 prefill，tmin=4096）与 code（超长 prefill，tmin=7500）
# 4 臂 × 10 种子 × 30 trials；隔离 /tmp + 增量合并
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled

MAIN=/mnt/f/文献/AgentOps/实验记录

is_done() {
  local f="$MAIN/optuna/$1/trials.csv"
  if [ -f "$f" ]; then
    local n
    n=$(($(wc -l < "$f") - 1))
    [ "$n" -ge 30 ] && return 0
  fi
  return 1
}

run_trace() {  # tag tokens_min trace_file
  local tag=$1 tmin=$2 trace=$3
  local rec="/tmp/agentops-s7-$tag"
  mkdir -p "$rec"
  for arm in N S M A; do
    for s in 1 2 3 4 5 6 7 8 9 10; do
      local name="s7-$tag-$arm-seed$s"
      if is_done "$name"; then echo "[$tag] skip $name"; continue; fi
      echo "[$tag] $arm s$s $(date +%H:%M:%S)"
      AGENTOPS_RECORDS="$rec" python -m agentops.tune --arm "$arm" --seed "$s" --n-trials 30 \
        --space-mode 5d --qps 12.0 --num-requests 384 \
        --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
        --tokens-min "$tmin" --length-trace "$trace" \
        --study-name "$name" || echo "!! fail $name"
      if [ -d "$rec/optuna/$name" ]; then
        rm -rf "$MAIN/optuna/$name"
        cp -r "$rec/optuna/$name" "$MAIN/optuna/"
      fi
    done
  done
  echo "[$tag] done $(date +%H:%M:%S)"
}

run_trace arxiv 4096 arxiv_summarization_stats_llama2_tokenizer_filtered_v2.csv &
T1=$!
run_trace code 7500 splitwise_code.csv &
T2=$!

wait $T1
wait $T2
echo "S7 TRANSFER DONE [$(date +%H:%M:%S)]"
