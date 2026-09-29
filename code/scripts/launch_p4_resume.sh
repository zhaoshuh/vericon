#!/usr/bin/env bash
# 以守护进程方式启动 P4 续跑（setsid 脱离会话，抗 harness shell 终止）
LOG=/mnt/f/文献/AgentOps/实验记录/P4-扫描日志.log
setsid nohup bash /mnt/f/文献/AgentOps/代码/scripts/run_p4_resume.sh > "$LOG" 2>&1 < /dev/null &
echo "launched pid=$!"
sleep 5
echo "---- log tail ----"
tail -n 8 "$LOG" 2>/dev/null || true
