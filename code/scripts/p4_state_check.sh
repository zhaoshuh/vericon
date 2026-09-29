#!/usr/bin/env bash
echo "== 进程 =="
pgrep -f agentops.tune | wc -l
echo "== 6d A s10 是否完成 =="
d=/mnt/f/文献/AgentOps/实验记录/optuna/p4-6d-q12-A-s10
if [ -f "$d/trials.csv" ]; then echo "trials=$(($(wc -l < $d/trials.csv) - 1))"; else echo "缺失"; fi
echo "== 主目录已完成 study（q8/q16）=="
ls -d /mnt/f/文献/AgentOps/实验记录/optuna/p4-5d-q*-*/ 2>/dev/null | xargs -n1 basename 2>/dev/null || echo "(无)"
echo "== 隔离目录 =="
for t in q8 q16; do
  n=$(ls -d /mnt/f/文献/AgentOps/实验记录/P4-并行-records-$t/optuna/p4-*/ 2>/dev/null | wc -l)
  echo "  P4-并行-records-$t: $n"
done
