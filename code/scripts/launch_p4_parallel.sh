#!/usr/bin/env bash
# 切换：杀掉串行续跑 → 启动并行收尾守护
LOG=/mnt/f/文献/AgentOps/实验记录/P4-扫描日志.log

echo "== kill 串行 daemon =="
pkill -f run_p4_resume.sh 2>/dev/null || true
pkill -f "agentops.tune" 2>/dev/null || true
sleep 3
echo "remaining tune procs: $(pgrep -f 'agentops.tune' | wc -l)"

echo "== 启动并行收尾 =="
setsid nohup bash /mnt/f/文献/AgentOps/代码/scripts/run_p4_parallel.sh >> "$LOG" 2>&1 < /dev/null &
echo "launched pid=$!"
sleep 8
echo "---- log tail ----"
tail -n 6 "$LOG" 2>/dev/null || true
