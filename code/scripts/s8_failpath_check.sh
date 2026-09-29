#!/usr/bin/env bash
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
B=/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench
M=/mnt/f/文献/AgentOps/代码/third_party/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
"$B" -m "$M" -t 4 -b 256 -ub 128 -fa off -ctv q8_0 -p 256 -n 16 -r 1 -o csv > /tmp/t1.txt 2>&1
echo "fa=off ctv=q8_0 rc=$?"
"$B" -m "$M" -t 4 -b 256 -ub 128 -fa on -ctv q8_0 -p 256 -n 16 -r 1 -o csv > /tmp/t2.txt 2>&1
echo "fa=on ctv=q8_0 rc=$?"
echo "--- t1 tail ---"
tail -2 /tmp/t1.txt
echo "--- t2 last ---"
tail -1 /tmp/t2.txt | cut -c1-200
