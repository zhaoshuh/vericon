#!/usr/bin/env bash
T=/mnt/f/文献/AgentOps/论文/latex/main.tex
echo "=== hyperref 配置 ==="
grep -n 'hyperref\|hypersetup\|hidelinks\|colorlinks' "$T" | head -10
echo ""
echo "=== PDF 链接注解检查（前几页） ==="
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
doc = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main.pdf")
for i in range(min(4, len(doc))):
    links = doc[i].get_links()
    if links:
        kinds = {}
        for l in links:
            kinds[l["kind"]] = kinds.get(l["kind"], 0) + 1
        print(f"p{i+1}: {len(links)} links, kinds={kinds}")
        for l in links[:3]:
            print("   ", {k: l.get(k) for k in ("kind", "uri", "file", "page", "from")})
PYEOF
