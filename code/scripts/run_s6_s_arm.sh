#!/usr/bin/env bash
# P6+② S 臂（SCOOT 式：人工规则 + 在线边界学习）：5d/q12，种子 1-20 × 30 trials
# 隔离 records 在 /tmp（快）；每 study 完成增量合并到主目录
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled

REC=/tmp/agentops-s6
MAIN=/mnt/f/文献/AgentOps/实验记录
mkdir -p "$REC"

SEEDS="${SEEDS:-1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20}"
TRIALS="${TRIALS:-30}"

for s in $SEEDS; do
  name="s6-S-seed$s"
  if [ -f "$MAIN/optuna/$name/trials.csv" ]; then
    n=$(($(wc -l < "$MAIN/optuna/$name/trials.csv") - 1))
    if [ "$n" -ge "$TRIALS" ]; then
      echo "[S] skip $name (已完成 $n)"
      continue
    fi
  fi
  echo "[S] seed=$s $(date +%H:%M:%S)"
  AGENTOPS_RECORDS="$REC" python -m agentops.tune --arm S --seed "$s" --n-trials "$TRIALS" \
    --space-mode 5d --qps 12.0 --num-requests 384 \
    --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
    --study-name "$name" || echo "!! fail $name"
  if [ -d "$REC/optuna/$name" ]; then
    rm -rf "$MAIN/optuna/$name"
    cp -r "$REC/optuna/$name" "$MAIN/optuna/"
  fi
done
echo "S6 S-ARM DONE [$(date +%H:%M:%S)]"
