#!/usr/bin/env bash
LOG='/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/run3.log'
L=$(wc -l < "$LOG" 2>/dev/null)
echo "log lines: $L (≈415 行 = 完成)"
tail -2 "$LOG" | cut -c1-120
echo "--- 各臂计数/非法 ---"
for a in N M A S; do
  c=$(grep -c "^$a s" "$LOG" 2>/dev/null)
  inv=$(grep "^$a s" "$LOG" | grep -c 'failed\|timeout')
  echo "  $a: $c trials, invalid=$inv"
done
echo "--- calibration ---"
cat '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/calibration-ext.csv' 2>/dev/null | tail -4
echo "--- S 学习事件 ---"
grep -c 'learns at' "$LOG" 2>/dev/null
pgrep -f s8c_llamacpp_ext.py >/dev/null && echo "running ✓" || echo "已结束"
