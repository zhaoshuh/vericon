#!/usr/bin/env bash
# P4 盘点：列出所有 p4 study 目录 + trial 数 + 修改时间；WSL 运行时长
echo "== WSL uptime =="
uptime
echo ""
echo "== p4 study 盘点 =="
for d in /mnt/f/文献/AgentOps/实验记录/optuna/p4-*/; do
  name=$(basename "$d")
  csv="$d/trials.csv"
  if [ -f "$csv" ]; then
    n=$(($(wc -l < "$csv") - 1))
  else
    n="no-csv"
  fi
  mt=$(date -r "$d" "+%H:%M")
  echo "$name  trials=$n  mtime=$mt"
done | sort
echo ""
echo "== 目录总数 =="
ls -d /mnt/f/文献/AgentOps/实验记录/optuna/p4-*/ | wc -l
