#!/usr/bin/env bash
echo "== tectonic 进程 =="
if pgrep -f "bin/tectonic" > /dev/null; then
  ps -o pid,etime,time,cmd -p "$(pgrep -f 'bin/tectonic' | head -1)"
  echo "状态: 运行中"
else
  echo "状态: 已结束"
fi
echo ""
echo "== 缓存大小 =="
du -sh "$HOME/.cache/tectonic" 2>/dev/null
echo ""
echo "== 编译产物/日志 =="
ls -la "/mnt/f/文献/AgentOps/论文/latex/" | grep -E "main\.(pdf|log)" || echo "(无 main.pdf / main.log)"
echo ""
echo "== compile 脚本输出 =="
cat "C:/Users/Administrator/.local/share/opencode/shell/2d71e05a1c1723d7e4033dd453f29f3c3d6f78af/sh_0e86988cf001Cbeacf6zF3yS0N.out" 2>/dev/null | tail -20 || true
