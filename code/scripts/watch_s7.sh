#!/usr/bin/env bash
# S7 看门狗
LOG='/mnt/f/文献/AgentOps/实验记录/S7-迁移日志.log'
for i in $(seq 1 180); do
  if grep -q 'S7 TRANSFER DONE' "$LOG" 2>/dev/null; then
    echo 'S7 TRANSFER DONE detected'
    exit 0
  fi
  sleep 60
done
echo 'watcher timeout (3h)'
