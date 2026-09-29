#!/usr/bin/env bash
# S2 验收脚本：vLLM 客户端自检 → 一条配置完整链路 → Optuna 小规模调优
set -euo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
cd "/mnt/f/文献/AgentOps/代码"
export WANDB_MODE=disabled

echo "== 1/3 vLLM 客户端逻辑自检（假 SSE 服务器，无需 GPU）=="
python -m agentops.backends.vllm_backend --selftest

echo ""
echo "== 2/3 一条配置的完整链路（配置 → 指标 → 成本）=="
python -m agentops.run_one \
  --max-num-seqs 64 --max-num-batched-tokens 2048 \
  --num-requests 128 --qps 8

echo ""
echo "== 3/3 Optuna 小规模调优 =="
python -m agentops.tune --n-trials 5 --study-name s2-smoke --num-requests 128

echo ""
echo "S2_SMOKE_ALL_DONE"
