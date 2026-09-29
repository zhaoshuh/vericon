#!/usr/bin/env bash
# P4 维度扩展扫描：
#   Phase A 维度曲线：2d / 6d @ qps12（5d@qps12 复用 s5-* 记录）
#   Phase B 负载稳健性：5d @ qps8 / qps16
# 用法（全量）：bash run_p4_sweep.sh
# 冒烟：MODES="6d" ARMS="N A" SEEDS="1" TRIALS="3" SKIP_LOAD=1 bash run_p4_sweep.sh
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd "/mnt/f/文献/AgentOps/代码"
export WANDB_MODE=disabled

ARMS="${ARMS:-N M A}"
SEEDS="${SEEDS:-1 2 3 4 5 6 7 8 9 10}"
TRIALS="${TRIALS:-30}"
MODES="${MODES:-2d 6d}"
QLIST="${QLIST:-8 16}"
SKIP_LOAD="${SKIP_LOAD:-0}"

COMMON="--num-requests 384 --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1"
START=$(date +%s)

# ---- Phase A：维度曲线（qps=12）----
for mode in $MODES; do
  for arm in $ARMS; do
    for s in $SEEDS; do
      echo ""
      echo "=== p4 dim mode=$mode arm=$arm seed=$s trials=$TRIALS [$(date +%H:%M:%S)] ==="
      python -m agentops.tune --arm "$arm" --seed "$s" --n-trials "$TRIALS" --space-mode "$mode" \
        --qps 12.0 $COMMON --study-name "p4-$mode-q12-$arm-s$s" || echo "!! fail $mode $arm $s"
    done
  done
done

# ---- Phase B：负载稳健性（5d @ qps 8/16）----
if [ "$SKIP_LOAD" != "1" ]; then
  for q in $QLIST; do
    for arm in $ARMS; do
      for s in $SEEDS; do
        echo ""
        echo "=== p4 load q=$q arm=$arm seed=$s trials=$TRIALS [$(date +%H:%M:%S)] ==="
        python -m agentops.tune --arm "$arm" --seed "$s" --n-trials "$TRIALS" --space-mode 5d \
          --qps "$q.0" $COMMON --study-name "p4-5d-q${q}-$arm-s$s" || echo "!! fail q$q $arm $s"
      done
    done
  done
fi

END=$(date +%s)
echo ""
echo "P4 SWEEP DONE in $(( (END-START)/60 )) min"
