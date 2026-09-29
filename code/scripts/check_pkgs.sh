#!/usr/bin/env bash
TEXDIR="$HOME/texlive/2026"
BIN="$TEXDIR/bin/x86_64-linux"
echo "== tlmgr 补装进度 =="
pgrep -f "tlmgr" > /dev/null && echo "补装进行中" || echo "补装已结束/未运行"
tail -4 /tmp/texlive_min.log 2>/dev/null
echo ""
echo "== 关键包检查 =="
for p in IEEEtran.cls booktabs.sty xcolor.sty textcomp.sty url.sty amsmath.sty graphicx.sty array.sty; do
  R=$("$BIN/kpsewhich" "$p" 2>/dev/null)
  if [ -n "$R" ]; then echo "  ✅ $p"; else echo "  ❌ $p"; fi
done
