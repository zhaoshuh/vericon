# -*- coding: utf-8 -*-
"""按"正文首次引用顺序"重排 thebibliography（IEEE 风格）+ 引用完整性检查"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"F:\文献\AgentOps\论文\latex\main.tex"
t = open(P, encoding="utf-8").read()

head, bib = t.split(r"\begin{thebibliography}", 1)
bib_body, tail = bib.split(r"\end{thebibliography}", 1)
bib_body = bib_body.lstrip()
if bib_body.startswith("{99}"):
    bib_body = bib_body[4:].lstrip("\n")

# 1) 提取 bibitem 块
items = {}
for m in re.finditer(r"\\bibitem\{([^}]+)\}", bib_body):
    key = m.group(1)
    start = m.start()
    items[key] = start
keys = list(items.keys())
# 按出现顺序切块
starts = sorted((v, k) for k, v in items.items())
blocks = {}
for i, (s, k) in enumerate(starts):
    e = starts[i + 1][0] if i + 1 < len(starts) else len(bib_body)
    blocks[k] = bib_body[s:e].rstrip() + "\n"

# 2) 正文首引顺序
order = []
for m in re.finditer(r"\\cite\{([^}]+)\}", head):
    for k in m.group(1).split(","):
        k = k.strip()
        if k not in order:
            order.append(k)

# 3) 检查
cited = set(order)
allk = set(keys)
missing_cite = sorted(allk - cited)   # 未被引用
ghost = sorted(cited - allk)          # 引用无 bibitem
print(f"bibitems={len(allk)}  cited={len(cited)}")
print("未被引用:", missing_cite if missing_cite else "无")
print("引用无定义:", ghost if ghost else "无")

if ghost or missing_cite:
    print("!! 先修复引用问题再重排")
    sys.exit(1)

# 4) 重排
new_bib = [blocks[k] for k in order]
out = head + r"\begin{thebibliography}{99}" + "\n\n" + "\n".join(new_bib) + "\n" + r"\end{thebibliography}" + tail
open(P, "w", encoding="utf-8").write(out)
print(f"已按首引顺序重排 {len(new_bib)} 条参考文献")
