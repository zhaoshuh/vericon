#!/usr/bin/env bash
python3 - <<'PY'
import re
p = '/mnt/f/文献/AgentOps/论文/latex/main.tex'
t = open(p, encoding='utf-8').read()
bibs = re.findall(r'\\bibitem\{([^}]+)\}', t)
cited = set()
for m in re.findall(r'\\cite\{([^}]+)\}', t):
    for k in m.split(','):
        cited.add(k.strip())
body = t.split(r'\begin{thebibliography}')[0]
cited_in_body = set()
for m in re.findall(r'\\cite\{([^}]+)\}', body):
    for k in m.split(','):
        cited_in_body.add(k.strip())
print('bibitems:', len(bibs))
print('正文引用的 key 数:', len(cited_in_body))
missing_cite = [b for b in bibs if b not in cited_in_body]
print('!! 从未在正文引用的文献:', missing_cite)
ghost = [c for c in cited_in_body if c not in bibs]
print('!! 引用了但无 bibitem:', ghost)
PY
