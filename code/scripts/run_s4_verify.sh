#!/usr/bin/env bash
# S4 轨道A 包装脚本（在 WSL 里跑）
# 用法: bash /mnt/f/文献/AgentOps/代码/scripts/run_s4_verify.sh [--limit 5] [--only C001]
set -e
PY="$HOME/.venvs/vllm-cpu/bin/python"
SCRIPT="/mnt/f/文献/AgentOps/代码/scripts/s4_verify_vllm.py"
exec "$PY" "$SCRIPT" "$@"
