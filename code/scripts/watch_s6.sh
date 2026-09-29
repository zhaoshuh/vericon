#!/usr/bin/env bash
# S6 S 臂看门狗
LOG='/mnt/f/文献/AgentOps/实验记录/S6-扫描日志.log'
for i in $(seq 1 180); do
  if grep -q 'S6 S-ARM DONE' "$LOG" 2>/dev/null; then
    echo 'S6 S-ARM DONE detected'
    exit 0
  fi
  sleep 60
done
echo 'watcher timeout (3h)'
