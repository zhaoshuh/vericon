#!/usr/bin/env bash
LOG='/mnt/f/文献/AgentOps/实验记录/P4-扫描日志.log'
echo "== 轨道完成标记 =="
grep -E '^\[(6d|q8|q16)\] done|^\[merge\]|P4 RESUME DONE' "$LOG" || echo "(无完成标记)"
echo ""
echo "== 隔离产物 =="
for d in /tmp/agentops-p4q8 /tmp/agentops-p4q16; do
  if [ -d "$d/optuna" ]; then
    echo "$d: $(ls -d $d/optuna/p4-*/ 2>/dev/null | wc -l) 个 study 目录"
  else
    echo "$d: 不存在"
  fi
done
echo ""
echo "== 主 optuna 目录 p4 计数 =="
ls -d /mnt/f/文献/AgentOps/实验记录/optuna/p4-*/ 2>/dev/null | wc -l
echo ""
echo "== 各相位完成数（主目录）=="
for phase in 2d-q12 6d-q12 5d-q8 5d-q16; do
  n=$(ls -d /mnt/f/文献/AgentOps/实验记录/optuna/p4-$phase-*/ 2>/dev/null | wc -l)
  echo "  $phase: $n"
done
echo ""
echo "== 6d A s10 是否完成 =="
d=/mnt/f/文献/AgentOps/实验记录/optuna/p4-6d-q12-A-s10
if [ -f "$d/trials.csv" ]; then echo "trials=$(($(wc -l < $d/trials.csv) - 1))"; else echo "缺失"; fi
echo ""
echo "== q8/q16 最后一屏日志 =="
grep -E '^\[(q8|q16)\]' "$LOG" | tail -6
