#!/usr/bin/env bash
LOG='/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/run2.log'
L=$(wc -l < "$LOG" 2>/dev/null)
echo "log lines: $L / ~306"
echo "--- 最近 2 行 ---"
tail -2 "$LOG" | cut -c1-120
echo "--- 各臂计数 ---"
for a in N M A; do
  c=$(grep -c "^$a s" "$LOG" 2>/dev/null)
  inv=$(grep "^$a s" "$LOG" | grep -c 'failed\|timeout')
  echo "  $a: $c trials, invalid=$inv"
done
echo "--- calibration ---"
cat '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/calibration.csv' 2>/dev/null
echo "--- 进程检查 ---"
pgrep -f s8b_llamacpp_control.py >/dev/null && echo "running ✓" || echo "已结束（或未运行）"
