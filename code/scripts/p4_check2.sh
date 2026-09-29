#!/usr/bin/env bash
LOG='/mnt/f/文献/AgentOps/实验记录/P4-扫描日志.log'
echo "== 完成标记 =="
grep -E 'P4 FINISH DONE|\[q8\] done|\[q16\] done' "$LOG" | tail -4
echo "== 进程数 =="
pgrep -f agentops.tune | wc -l
echo "== 各相位完成数 =="
for phase in 2d-q12 6d-q12 5d-q8 5d-q16; do
  n=$(ls -d /mnt/f/文献/AgentOps/实验记录/optuna/p4-$phase-*/ 2>/dev/null | wc -l)
  echo "  $phase: $n"
done
echo "== 最后 6 行轨道日志 =="
grep -E '^\[(6d|q8|q16)\]' "$LOG" | tail -6
