#!/usr/bin/env bash
echo "== 磁盘 =="
df -h "$HOME" | tail -1
echo "== venvs 占用 =="
du -sh "$HOME"/.venvs/* 2>/dev/null
echo "== vidur-fast =="
du -sh "$HOME"/vidur-fast 2>/dev/null
