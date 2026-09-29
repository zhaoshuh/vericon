#!/usr/bin/env bash
LAT=/mnt/f/文献/AgentOps/论文/latex
cp -f /tmp/mainbuild/main.pdf "$LAT/main-final.pdf" && echo "已写出 main-final.pdf"
ls -la "$LAT/main-final.pdf"
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
d = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main-final.pdf")
t = d[0].get_text()
print("页数:", len(d))
print("含 199 词新摘要:", "now dormant" in t)
print("含旧摘要:", "rendered dormant" in t)
print("附录已成正文小节:", "Artifact Availability" in "".join(p.get_text() for p in d))
PYEOF
