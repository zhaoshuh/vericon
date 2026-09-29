#!/usr/bin/env bash
echo "== 旧编译任务状态 =="
pgrep -f tectonic >/dev/null && echo "仍在运行" || echo "已结束"
ls -la "/mnt/f/文献/AgentOps/论文/latex/main.pdf" 2>/dev/null || echo "(无 main.pdf)"
echo ""
echo "== 结构复检 =="
python3 - <<'PY'
import re
p = '/mnt/f/文献/AgentOps/论文/latex/main.tex'
t = open(p, encoding='utf-8').read()
begins = re.findall(r'\\begin\{([^}]+)\}', t)
ends = re.findall(r'\\end\{([^}]+)\}', t)
from collections import Counter
cb, ce = Counter(begins), Counter(ends)
bad = [e for e in set(list(cb)+list(ce)) if cb[e] != ce[e]]
print('环境配对:', 'OK' if not bad else f'!! {bad}')
print('花括号:', t.count('{'), t.count('}'), 'OK' if t.count('{') == t.count('}') else '!!')
print('结尾:', 'OK' if t.rstrip().endswith('\\end{document}') else '!!')
print('bibitem 数:', len(re.findall(r'\\bibitem', t)))
PY
