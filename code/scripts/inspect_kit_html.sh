#!/usr/bin/env bash
F='/mnt/f/文献/AgentOps/实验记录/C1-人类盲标/标注工具.html'
echo "=== 关键 JS 行 ==="
grep -n 'const DATA\|function render\|render();\|localStorage\|function setV\|function exportCSV' "$F" | head -12
echo ""
echo "=== 脚本前 8 行 ==="
awk '/<script>/{f=1} f{print NR": "substr($0,1,110)} /const EXAMPLE/{if(f)exit}' "$F" | head -10
echo ""
echo "=== DATA 之后紧跟的 3 行（检查 JSON 是否被破坏） ==="
grep -n 'const DATA' "$F" | head -1
awk '/const DATA/{f=1; print substr($0,1,80)" ...[行太长已截断]"; getline; print NR": "substr($0,1,80); getline; print NR": "substr($0,1,80); exit}' "$F"
