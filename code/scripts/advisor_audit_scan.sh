#!/usr/bin/env bash
echo "=== 1) '导师' / 'advisor' 出现位置（排除 third_party） ==="
grep -rn '导师\|advisor' /mnt/f/文献/AgentOps --include='*.md' --include='*.json' --include='*.tex' --include='*.txt' 2>/dev/null | grep -v third_party | grep -v '.pre-a13' | head -30
echo ""
echo "=== 2) G1 记录中的相关小节 ==="
grep -n '导师\|复核' '/mnt/f/文献/AgentOps/实验记录/G1-约束抽检-第一批.md' 2>/dev/null | head -10
echo ""
echo "=== 3) run2 进度（尾部 3 行 + 计数） ==="
tail -3 '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/run2.log' 2>/dev/null | cut -c1-130
grep -c ' -> ' '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/run2.log' 2>/dev/null
echo "--- calibration ---"
cat '/mnt/f/文献/AgentOps/实验记录/S8-llamaCpp调优/calibration.csv' 2>/dev/null | tail -4
