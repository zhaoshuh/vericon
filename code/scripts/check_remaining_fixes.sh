#!/usr/bin/env bash
T="/mnt/f/文献/AgentOps/论文/latex/main.tex"
echo "== 残留 R2 旧声明检查（应为空） =="
grep -n "not enforced by any version\|over-assertion\|wrong from the start" "$T" || echo "  （已清空 ✅）"
echo ""
echo "== 其他待修数字 =="
grep -n "twelve configurations\|10\\\\% invalid\|24.1\\\\%\|48.3\\\\% \[46.7\|8{,}000+ configurations\|every disagreement\|150 doubly-audited" "$T" | head -12
