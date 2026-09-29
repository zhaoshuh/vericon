#!/usr/bin/env bash
echo "== processed_traces 目录 =="
ls -la "$HOME/vidur-fast/data/processed_traces/" 2>/dev/null | head -20
echo ""
echo "== 每个 trace 的头部与行数 =="
for f in "$HOME"/vidur-fast/data/processed_traces/*.csv; do
  [ -f "$f" ] || continue
  echo "---- $f"
  head -3 "$f"
  echo "   lines: $(wc -l < "$f")"
done
echo ""
echo "== vidur data 目录全貌 =="
find "$HOME/vidur-fast/data" -maxdepth 2 -type f 2>/dev/null | head -30
