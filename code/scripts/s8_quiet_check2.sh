#!/usr/bin/env bash
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
B=/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench
M=/mnt/f/文献/AgentOps/代码/third_party/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
for cfg in "4 128 128 off f16" "4 512 256 on f16" "3 512 128 on f16"; do
  set -- $cfg
  echo "== t=$1 b=$2 ub=$3 fa=$4 ctv=$5 =="
  "$B" -m "$M" -t $1 -b $2 -ub $3 -fa $4 -ctv $5 -p 256 -n 16 -r 1 2>/dev/null | grep -E 'pp 256|tg 16' | head -2
done
