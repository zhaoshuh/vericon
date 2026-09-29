#!/usr/bin/env bash
# P5 采样器补跑（seed 2/3）：独立 AGENTOPS_RECORDS 目录，与 P4 扫描完全隔离，
# 避免并发写 runs.csv（2026-09-27 损坏事故根因）。
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
export WANDB_MODE=disabled
export AGENTOPS_RECORDS="/tmp/agentops-p5run"
mkdir -p "$AGENTOPS_RECORDS"

cd /mnt/f/文献/AgentOps/代码
GRAPH="/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json,/mnt/f/文献/AgentOps/实验记录/P5-附加约束.json"

for s in 2 3; do
  echo "=== p5 sampler(隔离) 6d arm=A seed=$s [$(date +%H:%M:%S)] ==="
  python -m agentops.tune --arm A --seed "$s" --n-trials 30 --space-mode 6d \
    --qps 12.0 --num-requests 384 --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
    --sampler-graph "$GRAPH" --study-name "p5-6d-graph-A-s$s" || echo "!! fail s$s"
done

echo "=== 合并回主 records ==="
rm -rf /mnt/f/文献/AgentOps/实验记录/optuna/p5-6d-graph-A-s2 \
       /mnt/f/文献/AgentOps/实验记录/optuna/p5-6d-graph-A-s3
cp -r "$AGENTOPS_RECORDS/optuna/p5-6d-graph-A-s2" /mnt/f/文献/AgentOps/实验记录/optuna/
cp -r "$AGENTOPS_RECORDS/optuna/p5-6d-graph-A-s3" /mnt/f/文献/AgentOps/实验记录/optuna/
# 记录副本单独存放（避免与 P4 并发写主 runs.*）
rm -rf /mnt/f/文献/AgentOps/实验记录/P5-采样器补跑-records
cp -r "$AGENTOPS_RECORDS" /mnt/f/文献/AgentOps/实验记录/P5-采样器补跑-records
echo "P5 SAMPLER RERUN DONE"
