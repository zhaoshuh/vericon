#!/usr/bin/env bash
LOG=/mnt/f/文献/AgentOps/实验记录/S7-迁移日志.log
setsid nohup bash /mnt/f/文献/AgentOps/代码/scripts/run_s7_transfer.sh >> "$LOG" 2>&1 < /dev/null &
echo "launched pid=$!"
sleep 6
tail -n 4 "$LOG" 2>/dev/null || true
