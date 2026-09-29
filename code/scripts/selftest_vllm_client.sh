#!/usr/bin/env bash
# 无 GPU 自检：vLLM 客户端逻辑（假 SSE 服务器，验证 TTFT/ITL/指标汇总）
set -euo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
cd "/mnt/f/文献/AgentOps/代码"
exec python -m agentops.backends.vllm_backend --selftest
