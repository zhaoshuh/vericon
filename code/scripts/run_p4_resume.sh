#!/usr/bin/env bash
# P4 断点续跑：补齐 2d 缺口 + 6d 全量 + 5d q8/q16 负载稳健性
# 特性：新 record.py（文件锁+原子替换）、目标总数语义、日志写项目内
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled

# 0) 清理部分完成的 study（重跑全新 30 trials）
python - <<'PY'
import optuna
storage = "sqlite:////mnt/f/文献/AgentOps/实验记录/optuna/studies.db"
targets = [f"p4-2d-q12-N-s{s}" for s in (3, 5, 6, 7, 8, 9, 10)] + ["p4-2d-q12-A-s10"]
for t in targets:
    try:
        optuna.delete_study(study_name=t, storage=storage)
        print("deleted", t, flush=True)
    except Exception as e:
        print("skip", t, type(e).__name__, flush=True)
PY

run_study() {  # mode arm seed qps
  local mode=$1 arm=$2 seed=$3 qps=$4
  local qtag
  qtag=$(printf "%.0f" "$qps")
  echo ""
  echo "=== p4-resume $mode $arm s$seed q=$qtag [$(date +%H:%M:%S)] ==="
  python -m agentops.tune --arm "$arm" --seed "$seed" --n-trials 30 --space-mode "$mode" \
    --qps "$qps" --num-requests 384 --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
    --study-name "p4-$mode-q$qtag-$arm-s$seed" || echo "!! fail $mode $arm $seed"
}

# 1) 2d 补齐（N: s3/s5-s10；A: s10）
for s in 3 5 6 7 8 9 10; do run_study 2d N "$s" 12.0; done
run_study 2d A 10 12.0

# 2) 6d 全量（3 臂 × 10 种子）
for arm in N M A; do
  for s in 1 2 3 4 5 6 7 8 9 10; do run_study 6d "$arm" "$s" 12.0; done
done

# 3) 负载稳健性（5d @ qps 8 / 16）
for q in 8 16; do
  for arm in N M A; do
    for s in 1 2 3 4 5 6 7 8 9 10; do run_study 5d "$arm" "$s" "$q.0"; done
  done
done

echo ""
echo "P4 RESUME DONE [$(date +%H:%M:%S)]"
