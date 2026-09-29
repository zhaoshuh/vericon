#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf, re
d = pymupdf.open("/mnt/f/文献/AgentOps/论文/latex/main-final.pdf")
full = "\n".join(p.get_text() for p in d)
for kw in ("ARTIFACT AVAILABILITY", "Artifact Availability", "APPENDIX", "Appendix"):
    print(f"含 '{kw}':", kw in full)
m = re.search(r"(VIII|VII|IX)\.\s*\n?ARTIFACT AVAILABILITY", full)
print("小节标题匹配:", bool(m), m.group(0) if m else "")
print("引用渲染示例:", re.findall(r"§\s*[IVX]+", full)[:5])
PYEOF
