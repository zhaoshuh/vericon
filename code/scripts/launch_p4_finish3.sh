#!/usr/bin/env bash
# 切换 v3：杀掉当前 v2 收尾（F: 慢盘）→ 启动 v3（/tmp 快盘 + 增量合并）
LOG=/mnt/f/文献/AgentOps/实验记录/P4-扫描日志.log

echo "== kill v2 =="
pkill -f run_p4_finish.sh 2>/dev/null || true
pkill -f "agentops.tune" 2>/dev/null || true
sleep 3
echo "remaining tune procs: $(pgrep -f 'agentops.tune' | wc -l)"

echo "== 启动 v3 =="
setsid nohup bash /mnt/f/文献/AgentOps/代码/scripts/run_p4_finish3.sh >> "$LOG" 2>&1 < /dev/null &
echo "launched pid=$!"
sleep 8
echo "---- log tail ----"
tail -n 6 "$LOG" 2>/dev/null || true
