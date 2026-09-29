#!/usr/bin/env bash
LAT=/mnt/f/文献/AgentOps/论文/latex
TMP=/tmp/mainbuild
for f in main.pdf main.aux main.log main.out; do
  if cp -f "$TMP/$f" "$LAT/$f" 2>/dev/null; then
    echo "OK   $f"
  else
    echo "LOCKED $f （文件被 Windows 预览占用，无法写入）"
  fi
done
echo "--- 当前 latex 目录 main.pdf ---"
ls -la "$LAT/main.pdf" 2>/dev/null
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf, re, os
p = "/mnt/f/文献/AgentOps/论文/latex/main.pdf"
try:
    d = pymupdf.open(p)
    t = d[0].get_text()
    m = re.search(r"Hand-written configuration knowledge does not last.*?cost\.", t, re.S)
    print("PDF 首页摘要片段:", (m.group(0)[:120] + "...") if m else "（未匹配）")
    print("是否含新摘要（199 词版）:", "is now dormant" in t or "now dormant" in t)
except Exception as e:
    print("读取失败:", e)
PYEOF
