#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main.pdf")
total = 0
for i, page in enumerate(doc):
    links = page.get_links()
    if links:
        total += len(links)
        print(f"p{i+1}: {len(links)} links")
        for l in links[:2]:
            print("   ", {k: l.get(k) for k in ("kind", "uri", "file", "page")})
print("TOTAL links:", total)
# 抽查一页的所有标注
annots = list(doc[4].annots())
print("p5 annots:", [a.type for a in annots][:10])
PYEOF
echo "=== main.log 中 hyperref ==="
grep -c 'hyperref' /mnt/f/文献/AgentOps/论文/latex/main.log || echo 0
echo "=== 参考文献里的 URL 类文本 ==="
grep -n 'arxiv\|arXiv\|http' /mnt/f/文献/AgentOps/论文/latex/main.tex | head -8
