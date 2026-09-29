#!/usr/bin/env bash
# P4 进度检查
echo "== 已完成的 p4 study 目录（= trials.csv 已写出）=="
ls -d /mnt/f/文献/AgentOps/实验记录/optuna/p4-* 2>/dev/null | xargs -n1 basename | sort
echo ""
echo "== 当前运行的 study =="
for p in $(pgrep -f "agentops.tune"); do
  tr '\0' ' ' < "/proc/$p/cmdline" | grep -o -- "--study-name [^ ]*" || true
done
echo ""
echo "== 目录数统计 =="
ls -d /mnt/f/文献/AgentOps/实验记录/optuna/p4-* 2>/dev/null | wc -l
