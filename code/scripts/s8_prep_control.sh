#!/usr/bin/env bash
set -e
mkdir -p ~/models
if [ ! -f ~/models/qwen2.5-0.5b-instruct-q4_k_m.gguf ]; then
  echo "复制模型到 Linux 侧（一次性）..."
  time cp "/mnt/f/文献/AgentOps/代码/third_party/models/qwen2.5-0.5b-instruct-q4_k_m.gguf" ~/models/
fi
ls -la ~/models/
cd /mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优
if [ ! -f trials-run1-uncontrolled.csv ]; then
  cp trials.csv trials-run1-uncontrolled.csv
  echo "已备份 run1 -> trials-run1-uncontrolled.csv"
fi
ls
# 快速验证本地模型加载速度
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
B=/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench
time "$B" -m ~/models/qwen2.5-0.5b-instruct-q4_k_m.gguf -t 4 -b 256 -ub 128 -fa on -ctv f16 -p 256 -n 16 -r 1 2>/dev/null | awk -F'|' '/pp256/{gsub(/ /,"",$8); print "pp256 =", $8}'
