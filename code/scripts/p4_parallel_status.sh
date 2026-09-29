#!/usr/bin/env bash
echo "== tune 进程数 =="
pgrep -f "agentops.tune" | wc -l
echo "== 各进程 study =="
for p in $(pgrep -f "agentops.tune"); do
  tr '\0' ' ' < "/proc/$p/cmdline" | grep -o -- "--study-name [^ ]*"
done
echo "== 轨道日志行 =="
grep -E '^\[(6d|q8|q16)\]' /mnt/f/文献/AgentOps/实验记录/P4-扫描日志.log | tail -6
