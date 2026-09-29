#!/usr/bin/env bash
# 查进程身份 + 在读什么文件
PID=$(pgrep -f "agentops" | head -1)
echo "PID=${PID:-<无>}"
if [ -n "${PID:-}" ]; then
  echo "--- cmdline ---"; tr '\0' ' ' < "/proc/$PID/cmdline"; echo
  echo "--- cwd ---"; readlink "/proc/$PID/cwd"
  echo "--- 环境(AGENTOPS*) ---"; tr '\0' '\n' < "/proc/$PID/environ" | grep -E "AGENTOPS|WANDB" || echo "(无)"
  echo "--- 打开的文件 ---"; ls -l "/proc/$PID/fd" 2>/dev/null | sed 's/.*-> //' | sort -u | head -15
  echo "--- io 变化（5 秒） ---"
  A=$(awk '/read_bytes/{print $2}' "/proc/$PID/io"); U1=$(awk '{print $14}' "/proc/$PID/stat")
  sleep 5
  B=$(awk '/read_bytes/{print $2}' "/proc/$PID/io" 2>/dev/null); U2=$(awk '{print $14}' "/proc/$PID/stat" 2>/dev/null)
  echo "read_bytes: $A -> $B"
  echo "utime ticks: $U1 -> $U2"
fi
