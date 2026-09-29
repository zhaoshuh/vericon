#!/usr/bin/env bash
T="/mnt/f/文献/AgentOps/论文/latex/main.tex"
echo "== R2 相关声明位置 =="
grep -n "not enforced by any version\|over-assertion\|wrong from the start\|zero source-level hits\|two of SCOOT" "$T"
echo ""
echo "== Table II R2 行 =="
grep -n "chunked-prefill \$\$\\\\perp\$\$\|no mutual-exclusion" "$T"
