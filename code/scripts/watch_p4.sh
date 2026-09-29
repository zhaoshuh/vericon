#!/usr/bin/env bash
# P4 续跑看门狗：完成即退出（用于 harness 通知）
LOG='/mnt/f/文献/AgentOps/实验记录/P4-扫描日志.log'
for i in $(seq 1 420); do
  if grep -q 'P4 RESUME DONE' "$LOG" 2>/dev/null; then
    echo 'P4 RESUME DONE detected'
    exit 0
  fi
  sleep 60
done
echo 'watcher timeout (7h)'
