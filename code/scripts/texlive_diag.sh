#!/usr/bin/env bash
echo "== 临时下载文件明细 =="
ls -la /tmp/M2*/ | head -12
echo ""
echo "== 网卡流量（10 秒差值） =="
R1=$(cat /sys/class/net/eth0/statistics/rx_bytes 2>/dev/null || echo 0)
sleep 10
R2=$(cat /sys/class/net/eth0/statistics/rx_bytes 2>/dev/null || echo 0)
echo "rx delta: $((R2 - R1)) bytes/10s"
echo ""
echo "== install-tl 进程 CPU/状态 =="
ps -o pid,stat,etime,time,rss,cmd -C perl 2>/dev/null | head -3
echo ""
echo "== 子进程 =="
ps --ppid "$(pgrep -f install-tl | head -1)" -o pid,cmd 2>/dev/null | head -5
