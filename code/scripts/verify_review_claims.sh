#!/usr/bin/env bash
T=/mnt/f/文献/AgentOps/论文/latex/main.tex
echo "=== 1) 0.5B / 1.5B 出现处 ==="
grep -n '0\.5B\|1\.5B\|Qwen2\.5' "$T" | head -8
echo ""
echo "=== 2) 6-D A 成本 30.00 / 29.8 ==="
grep -n '29\.8\|30\.00\|30\.0 ' "$T" | head -8
echo ""
echo "=== 3) S 臂非法率 9.5 / 10% ==="
grep -n '9\.5\\%\|invalid rate 10\|10\\% invalid' "$T" | head -6
echo ""
echo "=== 4) 58.350 / 58.80 / 58.35 ==="
grep -n '58\.3' "$T" | head -6
echo ""
echo "=== 5) seven/eight 类型数 ==="
grep -n 'Seven types\|seven types\|eight types\|8 types\|7 types' "$T" | head -5
