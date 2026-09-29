#!/usr/bin/env bash
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
BIN="/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194"
echo "== llama-cli --version =="
"$BIN/llama-cli" --version 2>&1 | head -5
echo "== llama-bench --version =="
"$BIN/llama-bench" --version 2>&1 | head -3
echo "== llama-server --version =="
"$BIN/llama-server" --version 2>&1 | head -3
