#!/usr/bin/env bash
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
BENCH="/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench"
MODEL="/mnt/f/文献/AgentOps/代码/third_party/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
echo "== 关键参数支持检查 =="
"$BENCH" --help 2>&1 | grep -E "^\s+-(t|b|ub|fa|ctk|ctv|p|n|r|o)\b" | head -20
echo ""
echo "== 冒烟：一次基准（默认线程） =="
"$BENCH" -m "$MODEL" -p 128 -n 16 -r 1 -o csv 2>&1 | tail -6
echo ""
echo "== 冒烟：q8_0 V cache + 无 fa（应失败） =="
"$BENCH" -m "$MODEL" -p 128 -n 16 -r 1 -fa off -ctv q8_0 2>&1 | tail -4
echo "exit=$?"
