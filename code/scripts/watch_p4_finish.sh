#!/usr/bin/env bash
# P4 收尾看门狗（v2）：等待 P4 FINISH DONE
LOG='/mnt/f/文献/AgentOps/实验记录/P4-扫描日志.log'
for i in $(seq 1 300); do
  if grep -q 'P4 FINISH DONE' "$LOG" 2>/dev/null; then
    echo 'P4 FINISH DONE detected'
    exit 0
  fi
  sleep 60
done
echo 'watcher timeout (5h)'
