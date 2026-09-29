#!/usr/bin/env bash
CSV='/mnt/f/文献/AgentOps/实验记录/P4-并行-records-q8/optuna/p4-5d-q8-N-s2/trials.csv'
if [ -f "$CSV" ]; then
  echo "== 行数 =="; echo $(($(wc -l < "$CSV") - 1))
  echo "== 前 3 行时间 =="; cut -d, -f1,3,4 "$CSV" | head -4
  echo "== 后 3 行时间 =="; cut -d, -f1,3,4 "$CSV" | tail -3
else
  echo "无 $CSV"
fi
echo ""
echo "== q8 隔离 records 的 study 列表 =="
ls /mnt/f/文献/AgentOps/实验记录/P4-并行-records-q8/optuna/ 2>/dev/null
