#!/usr/bin/env bash
echo "=== README-投稿包 中与新进展相关的行 ==="
grep -n 'C1\|C2\|人工\|签名\|签核\|复核' '/mnt/f/文献/AgentOps/论文/latex/README-投稿包.md' 2>/dev/null | head -10
echo ""
echo "=== trials CSV 一致性 ==="
cd /mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优
md5sum trials.csv trials-run1-uncontrolled.csv trials-control.csv 2>/dev/null
echo ""
echo "=== 产物清单 ==="
ls -la /mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/ | awk '{print $5, $9}' | tail -12
