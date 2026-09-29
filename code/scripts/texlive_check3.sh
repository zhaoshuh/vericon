#!/usr/bin/env bash
TEXDIR="$HOME/texlive/2026"
echo "== install-tl 进程 =="
if pgrep -f "install-tl" > /dev/null; then
  echo "运行中 (elapsed: $(ps -o etime= -p "$(pgrep -f 'perl ./install-tl' | head -1)" 2>/dev/null | tr -d ' '))"
else
  echo "已结束"
fi
echo ""
echo "== 安装日志尾部 =="
tail -6 /tmp/texlive_min.log 2>/dev/null || echo "(无日志)"
echo ""
echo "== texlive 目录大小 =="
du -sh "$TEXDIR" 2>/dev/null || echo "(不存在)"
echo ""
echo "== pdflatex =="
ls "$TEXDIR/bin/x86_64-linux/pdflatex" 2>/dev/null && echo "已就位 ✅" || echo "(尚无)"
