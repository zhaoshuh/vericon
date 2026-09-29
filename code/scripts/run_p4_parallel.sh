#!/usr/bin/env bash
# P4 并行收尾：
#   Phase A（串行，主 records）：6d 余量（M s6-s10, A s1-s10）
#   Phase B（并行，隔离 records）：q8 / q16 各 30 个 study
#   最后合并隔离产物回主目录；输出含 "P4 RESUME DONE" 以便看门狗识别
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled

MAIN_REC=/mnt/f/文献/AgentOps/实验记录
Q8_REC=/tmp/agentops-p4q8
Q16_REC=/tmp/agentops-p4q16
mkdir -p "$Q8_REC" "$Q16_REC"

# 0) 清理 6d 部分 study（M-s6 被杀时未完成）
python - <<'PY'
import optuna
storage = "sqlite:////mnt/f/文献/AgentOps/实验记录/optuna/studies.db"
try:
    optuna.delete_study(study_name="p4-6d-q12-M-s6", storage=storage)
    print("deleted p4-6d-q12-M-s6", flush=True)
except Exception as e:
    print("skip M-s6", type(e).__name__, flush=True)
PY

run_one() {  # records_dir mode arm seed qps
  local rec=$1 mode=$2 arm=$3 seed=$4 qps=$5
  local qtag
  qtag=$(printf "%.0f" "$qps")
  AGENTOPS_RECORDS="$rec" python -m agentops.tune --arm "$arm" --seed "$seed" --n-trials 30 \
    --space-mode "$mode" --qps "$qps" --num-requests 384 \
    --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
    --study-name "p4-$mode-q$qtag-$arm-s$seed" || echo "!! fail $mode $arm $seed"
}

# ---- Phase B：q8 / q16 并行（后台子 shell）----
(
  echo "[q8] start $(date +%H:%M:%S)"
  for arm in N M A; do
    for s in 1 2 3 4 5 6 7 8 9 10; do
      echo "[q8] $arm s$s $(date +%H:%M:%S)"
      run_one "$Q8_REC" 5d "$arm" "$s" 8.0
    done
  done
  echo "[q8] done $(date +%H:%M:%S)"
) &
Q8_PID=$!
(
  echo "[q16] start $(date +%H:%M:%S)"
  for arm in N M A; do
    for s in 1 2 3 4 5 6 7 8 9 10; do
      echo "[q16] $arm s$s $(date +%H:%M:%S)"
      run_one "$Q16_REC" 5d "$arm" "$s" 16.0
    done
  done
  echo "[q16] done $(date +%H:%M:%S)"
) &
Q16_PID=$!

# ---- Phase A：6d 余量（主 records，串行）----
echo "[6d] start $(date +%H:%M:%S)"
for s in 6 7 8 9 10; do
  echo "[6d] M s$s $(date +%H:%M:%S)"
  run_one "$MAIN_REC" 6d M "$s" 12.0
done
for s in 1 2 3 4 5 6 7 8 9 10; do
  echo "[6d] A s$s $(date +%H:%M:%S)"
  run_one "$MAIN_REC" 6d A "$s" 12.0
done
echo "[6d] done $(date +%H:%M:%S)"

wait $Q8_PID
wait $Q16_PID

# ---- 合并隔离产物 ----
echo "[merge] $(date +%H:%M:%S)"
for d in "$Q8_REC"/optuna/p4-* "$Q16_REC"/optuna/p4-*; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  rm -rf "$MAIN_REC/optuna/$name"
  cp -r "$d" "$MAIN_REC/optuna/"
done
rm -rf "$MAIN_REC/P4-并行-records-q8" "$MAIN_REC/P4-并行-records-q16"
cp -r "$Q8_REC" "$MAIN_REC/P4-并行-records-q8"
cp -r "$Q16_REC" "$MAIN_REC/P4-并行-records-q16"

echo "P4 RESUME DONE (parallel) [$(date +%H:%M:%S)]"
