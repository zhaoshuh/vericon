#!/usr/bin/env bash
echo "== /tmp 下载目录 =="
for d in /tmp/M2*; do
  [ -d "$d" ] || continue
  echo "$d: $(du -sh "$d" 2>/dev/null | cut -f1), files=$(find "$d" -type f | wc -l)"
done
echo ""
echo "== 连接 =="
ss -tn 2>/dev/null | grep ESTAB | head -3
echo ""
echo "== 30 秒增长率 =="
D=$(ls -d /tmp/M2* 2>/dev/null | head -1)
A=$(du -sb "$D" 2>/dev/null | cut -f1)
sleep 30
B=$(du -sb "$D" 2>/dev/null | cut -f1)
echo "before=$A after=$B  (diff=$((B - A)) bytes/30s)"
echo ""
echo "== texlive 目录 =="
du -sh "$HOME/texlive" 2>/dev/null
