#!/usr/bin/env bash
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
BIN="/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194"
echo "== conversation / single-turn / load-mode =="
"$BIN/llama-cli" --help 2>&1 | grep -iE "conversation|single-turn|no-cnv|load-mode|mlock" | head -20
