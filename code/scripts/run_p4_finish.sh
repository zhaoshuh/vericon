#!/usr/bin/env bash
# P4 收尾（v2，抗重启版）：
#   - q8/q16 双轨并行，隔离 records 放【项目盘】；每完成一个 study 立即增量拷贝到主 optuna 目录
#   - 6d A s10 补跑（主 records）
#   - 幂等：已完成的 study 自动跳过
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled

MAIN=/mnt/f/文献/AgentOps/实验记录

is_done() {  # study_name
  local f="$MAIN/optuna/$1/trials.csv"
  if [ -f "$f" ]; then
    local n
    n=$(($(wc -l < "$f") - 1))
    [ "$n" -ge 30 ] && return 0
  fi
  return 1
}

merge_study() {  # records_dir study_name
  local rec=$1 name=$2
  if [ -d "$rec/optuna/$name" ]; then
    rm -rf "$MAIN/optuna/$name"
    cp -r "$rec/optuna/$name" "$MAIN/optuna/"
  fi
}

run_track() {  # qtag
  local qtag=$1
  local rec="$MAIN/P4-并行-records-q$qtag"
  mkdir -p "$rec"
  for arm in N M A; do
    for s in 1 2 3 4 5 6 7 8 9 10; do
      local name="p4-5d-q$qtag-$arm-s$s"
      if is_done "$name"; then echo "[q$qtag] skip $name (已完成)"; continue; fi
      echo "[q$qtag] $arm s$s $(date +%H:%M:%S)"
      AGENTOPS_RECORDS="$rec" python -m agentops.tune --arm "$arm" --seed "$s" --n-trials 30 \
        --space-mode 5d --qps "$qtag.0" --num-requests 384 \
        --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
        --study-name "$name" || echo "!! fail $name"
      merge_study "$rec" "$name"
    done
  done
  echo "[q$qtag] done $(date +%H:%M:%S)"
}

# ---- 双轨并行 ----
run_track 8 &
Q8=$!
run_track 16 &
Q16=$!

# ---- 6d A s10 补跑（主 records）----
name="p4-6d-q12-A-s10"
if is_done "$name"; then
  echo "[6d] skip $name (已完成)"
else
  echo "[6d] A s10 $(date +%H:%M:%S)"
  python -m agentops.tune --arm A --seed 10 --n-trials 30 --space-mode 6d \
    --qps 12.0 --num-requests 384 --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
    --study-name "$name" || echo "!! fail $name"
fi

wait $Q8
wait $Q16
echo "P4 FINISH DONE [$(date +%H:%M:%S)]"
