#!/usr/bin/env bash
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
BIN="/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194"
echo "===== llama-cli help (关键参数) ====="
"$BIN/llama-cli" --help 2>&1 | grep -E "^\s+-(b|ub|c|k|np|ngl|fa|t|ctk|ctv|m)[, ]|batch-size|ubatch|ctx-size|keep|parallel|gpu-layers|flash|mlock|threads|kv-type|cache-type" | head -40
echo ""
echo "===== llama-server help (关键参数) ====="
"$BIN/llama-server" --help 2>&1 | grep -E "parallel|ctx-size|batch-size|ubatch|keep|flash|threads" | head -20
