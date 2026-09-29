#!/usr/bin/env bash
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
BIN="/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194"
MODEL="/mnt/f/文献/AgentOps/代码/third_party/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
echo "== -b 128 -ub 256 verbose grep =="
"$BIN/llama-cli" -m "$MODEL" -p hi -n 4 -st -b 128 -ub 256 -lv 1 2>&1 | grep -iE "ubatch|clamp|batch" | head -15
echo "== -c 64 long prompt grep =="
"$BIN/llama-cli" -m "$MODEL" -c 64 -n 4 -st -p "abcdefghijklmnopqrstuvwxyz0123456789 abcdefghijklmnopqrstuvwxyz0123456789 abcdefghijklmnopqrstuvwxyz0123456789" -lv 1 2>&1 | grep -iE "truncat|too long|exceed|n_ctx|context" | head -15
