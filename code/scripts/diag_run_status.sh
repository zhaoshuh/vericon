#!/usr/bin/env bash
# 查看当前 run_one 进程状态 + 最新产物目录
source "$HOME/miniconda3/etc/profile.d/conda.sh" >/dev/null 2>&1 || true
PID=$(pgrep -f "python -m agentops.run_one" | head -1)
echo "PID=${PID:-<无>}"
if [ -n "${PID:-}" ]; then
  grep -E "^State" "/proc/$PID/status"
  awk '{printf "utime=%.1fs stime=%.1fs rss=%.0fMB\n", $14/100, $15/100, $24*4/1024}' "/proc/$PID/stat"
  cat "/proc/$PID/io" | grep -E "^(rchar|read_bytes)" | tr '\n' ' '; echo
fi
echo "--- 最新仿真输出 ---"
ls -dt "/mnt/f/文献/AgentOps/实验记录/仿真输出/"*/ 2>/dev/null | head -2
echo "--- 预测器磁盘缓存 ---"
ls -la "$HOME/vidur-fast/cache" 2>/dev/null | tail -5
