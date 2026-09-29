#!/usr/bin/env bash
# 诊断正在运行的 run_one 进程：状态 / IO / 打开的文件
PID=$(pgrep -f "python -m agentops.run_one" | head -1)
echo "PID=${PID:-<无>}"
if [ -n "${PID:-}" ]; then
  echo "--- status ---"
  grep -E "^(State|VmRSS|Threads)" "/proc/$PID/status"
  echo "--- io（rchar=读字节, read_bytes=磁盘读） ---"
  cat "/proc/$PID/io" | grep -E "^(rchar|read_bytes|write_bytes|cancelled_write_bytes)"
  echo "--- wchan ---"
  cat "/proc/$PID/wchan"; echo
  echo "--- 打开的文件（前 12 个） ---"
  ls -l "/proc/$PID/fd" 2>/dev/null | head -12
fi
echo "--- 最新仿真输出目录 ---"
LATEST=$(ls -dt "/mnt/f/文献/AgentOps/实验记录/仿真输出/"*/ 2>/dev/null | head -1)
echo "$LATEST"
ls -la "$LATEST" 2>/dev/null | head -12
echo "--- vidur/cache ---"
ls -la "/mnt/f/文献/AgentOps/代码/third_party/vidur/cache" 2>/dev/null | head -10
