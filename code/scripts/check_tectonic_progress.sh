#!/usr/bin/env bash
echo "== tectonic 缓存目录 =="
for d in "$HOME/.cache/Tectonic" "$HOME/.local/share/tectonic" "$HOME/.cache/tectonic"; do
  if [ -d "$d" ]; then
    echo "$d: $(du -sh "$d" 2>/dev/null | cut -f1)"
    find "$d" -name "*.ttb" -o -name "*.tar" 2>/dev/null | head -3
  fi
done
echo ""
echo "== 网络连接（tectonic 相关进程） =="
ps aux | grep -i tectonic | grep -v grep | head -3
echo ""
echo "== 30 秒后再看缓存大小（检测增长） =="
B=$(du -sb "$HOME/.cache/Tectonic" 2>/dev/null | cut -f1)
sleep 30
A=$(du -sb "$HOME/.cache/Tectonic" 2>/dev/null | cut -f1)
echo "before=$B after=$A"
