#!/usr/bin/env bash
echo "== 日志中的 tlmgr 行 =="
grep -a "tlmgr\|Trying to load\|installation\|Installing\|package" /tmp/texlive_min.log 2>/dev/null | tail -8
echo ""
echo "== curl 子进程 =="
ps aux | grep -E "curl|tlmgr" | grep -v grep | head -5
echo ""
echo "== 网络活动（10 秒） =="
R1=$(cat /sys/class/net/eth0/statistics/rx_bytes 2>/dev/null || echo 0)
sleep 10
R2=$(cat /sys/class/net/eth0/statistics/rx_bytes 2>/dev/null || echo 0)
echo "rx delta: $((R2 - R1)) bytes/10s"
echo ""
echo "== texlive 目录大小（60 秒变化） =="
A=$(du -sb "$HOME/texlive/2026" 2>/dev/null | cut -f1)
sleep 60
B=$(du -sb "$HOME/texlive/2026" 2>/dev/null | cut -f1)
echo "before=$((A/1048576))MB after=$((B/1048576))MB diff=$(( (B-A)/1024 ))KB/min"
