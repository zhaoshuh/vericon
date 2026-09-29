#!/usr/bin/env bash
F='/mnt/f/文献/AgentOps/实验记录/C1-人类盲标/标注工具.html'
echo "== 占位符残留检查 =="
grep -c 'NNN\|ITEMJSON\|EXAMPLEHTML' "$F" || echo "0 (clean)"
echo "== 结构检查 =="
grep -c '<div id="list">' "$F"
grep -c 'function exportCSV' "$F"
grep -o '配置约束站点盲标（共 [0-9]* 项）' "$F" | head -1
echo "== 数据项数 =="
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import re
t = open('/mnt/f/文献/AgentOps/实验记录/C1-人类盲标/标注工具.html', encoding='utf-8').read()
m = re.search(r'const DATA = (\[.*?\]);\n', t, re.S)
import json
d = json.loads(m.group(1))
print("items:", len(d), "| first id:", d[0]['id'], "| has context:", len(d[0]['context']), "lines")
PYEOF
