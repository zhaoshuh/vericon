#!/usr/bin/env bash
echo "== pdflatex 是否可用 =="
which pdflatex || echo "(无 pdflatex)"
echo ""
echo "== LaTeX 结构自检 =="
python3 - <<'PY'
import re
p = '/mnt/f/文献/AgentOps/论文/latex/main.tex'
t = open(p, encoding='utf-8').read()
# 环境配对
begins = re.findall(r'\\begin\{([^}]+)\}', t)
ends = re.findall(r'\\end\{([^}]+)\}', t)
from collections import Counter
cb, ce = Counter(begins), Counter(ends)
bad = False
for env in set(list(cb) + list(ce)):
    if cb[env] != ce[env]:
        print(f'  !! 环境不配对: {env}: begin={cb[env]} end={ce[env]}')
        bad = True
if not bad:
    print('  begin/end 环境全部配对 ✓')
# label/ref 匹配
labels = set(re.findall(r'\\label\{([^}]+)\}', t))
refs = set(re.findall(r'\\ref\{([^}]+)\}', t))
missing = refs - labels
unused = labels - refs
print(f'  labels={len(labels)} refs={len(refs)}')
if missing:
    print('  !! 引用无定义:', sorted(missing))
if unused:
    print('  (未引用 label:', sorted(unused), ')')
# 花括号粗查
ob, cb2 = t.count('{'), t.count('}')
print(f'  花括号: {{ = {ob}, }} = {cb2}  ({"平衡" if ob == cb2 else "!! 不平衡"})')
# 结尾
print('  结尾 \\end{document}:', '✓' if t.rstrip().endswith('\\end{document}') else '!! 缺失')
# 图片引用
import os
imported = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', t)
for f in sorted(set(imported)):
    fp = os.path.join('/mnt/f/文献/AgentOps/论文/latex', f)
    print(f'  图 {f}: {"存在" if os.path.exists(fp) else "!! 缺失"}')
PY
