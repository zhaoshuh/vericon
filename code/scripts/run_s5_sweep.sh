#!/usr/bin/env bash
# S5 全量三臂扫描：3 臂 × 20 种子 × 30 trials（可中断续跑；study 名唯一，Optuna load_if_exists）
# 用法：bash run_s5_sweep.sh            （默认全量）
#      ARMS="N" SEEDS="1 2" TRIALS=5 bash run_s5_sweep.sh   （子集）
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd "/mnt/f/文献/AgentOps/代码"
export WANDB_MODE=disabled

ARMS="${ARMS:-N M A}"
SEEDS="${SEEDS:-1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20}"
TRIALS="${TRIALS:-30}"

# 标定后的工作负载（见 S5-实验设计-v1.md §4 与容量探针记录）：
#   qps=12（容量 ~9.4 rps 以上，排队区）、384 请求、SLO TTFT p90<=1.0s / TPOT p90<=0.1s
COMMON="--space-mode 5d --qps 12.0 --num-requests 384 --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1"

START=$(date +%s)
for arm in $ARMS; do
  for s in $SEEDS; do
    echo ""
    echo "=== s5 arm=$arm seed=$s trials=$TRIALS  [$(date +%H:%M:%S)] ==="
    python -m agentops.tune --arm "$arm" --seed "$s" --n-trials "$TRIALS" \
        $COMMON --study-name "s5-$arm-seed$s" || echo "!! arm=$arm seed=$s 失败（继续）"
  done
done
END=$(date +%s)
echo ""
echo "S5 SWEEP DONE in $(( (END-START)/60 )) min"
