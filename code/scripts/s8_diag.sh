#!/usr/bin/env bash
echo "== load =="
uptime
echo "== 占用 CPU 的前 8 进程 =="
ps aux --sort=-%cpu | head -9
echo "== 遗留 llama/python 进程 =="
pgrep -fa 'llama|s8_|c4_|c1_' | head -10
echo "== WSL 电源/频率信息（可能不可用）=="
cat /sys/class/power_supply/AC*/online 2>/dev/null || echo "AC info n/a"
grep -m1 'cpu MHz' /proc/cpuinfo
echo "== 连测 3 次同一配置（看稳定性）=="
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
B=/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench
M=/mnt/f/文献/AgentOps/代码/third_party/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
for i in 1 2 3; do
  "$B" -m "$M" -t 4 -b 128 -ub 128 -fa off -ctv f16 -p 256 -n 16 -r 1 2>/dev/null | awk '/pp256/{print "pp256 =", $NF, $(NF-1), $(NF-2)}'
done
