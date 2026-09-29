#!/usr/bin/env bash
# 启动 P4 收尾（v2）守护进程
LOG=/mnt/f/文献/AgentOps/实验记录/P4-扫描日志.log
setsid nohup bash /mnt/f/文献/AgentOps/代码/scripts/run_p4_finish.sh >> "$LOG" 2>&1 < /dev/null &
echo "launched pid=$!"
sleep 8
tail -n 8 "$LOG" 2>/dev/null || true
