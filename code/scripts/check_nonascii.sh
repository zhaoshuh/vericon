#!/usr/bin/env bash
echo "== main.tex 中的非 ASCII 字符（带行号） =="
python3 - <<'PY'
p = '/mnt/f/文献/AgentOps/论文/latex/main.tex'
lines = open(p, encoding='utf-8').read().splitlines()
from collections import Counter
cnt = Counter()
for i, l in enumerate(lines, 1):
    bad = [(ch, ord(ch)) for ch in l if ord(ch) > 127]
    if bad:
        chars = ' '.join(f'{ch}(U+{o:04X})' for ch, o in bad)
        print(f'{i}: {chars}  | {l.strip()[:90]}')
        for ch, o in bad:
            cnt[ch] += 1
print()
print('汇总:', dict(cnt))
PY
echo ""
echo "== tectonic 进程 =="
pgrep -f tectonic >/dev/null && echo "编译仍在运行" || echo "无 tectonic 进程"
ls -la "/mnt/f/文献/AgentOps/论文/latex/main.pdf" 2>/dev/null || echo "(main.pdf 尚不存在)"
