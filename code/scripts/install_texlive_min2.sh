#!/usr/bin/env bash
# 修正版精简安装（补全 TEXMF 变量，全部指向用户目录）
set -uo pipefail
MIRROR="https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/tlnet"
TEXDIR="$HOME/texlive/2026"

pkill -f install-tl 2>/dev/null || true
sleep 1
rm -rf "$TEXDIR" /tmp/M2* 2>/dev/null || true

cd /tmp/install-tl-*/
cat > tl-min.profile <<EOF
selected_scheme scheme-basic
TEXDIR $TEXDIR
TEXMFHOME $TEXDIR/texmf
TEXMFLOCAL $TEXDIR/texmf-local
TEXMFSYSCONFIG $TEXDIR/texmf-config
TEXMFSYSVAR $TEXDIR/texmf-var
TEXMFVAR $TEXDIR/texmf-var
TEXMFCONFIG $TEXDIR/texmf-config
instopt_adjustpath 0
instopt_adjustrepo 0
tlpdbopt_autobackup 0
EOF

echo "== profile =="
cat tl-min.profile
echo ""
echo "== 安装 scheme-basic =="
setsid nohup ./install-tl -profile tl-min.profile -repository "$MIRROR" -no-interaction > /tmp/texlive_min.log 2>&1 &
PID=$!
echo "pid=$PID"

for i in $(seq 1 90); do
  if ! kill -0 "$PID" 2>/dev/null; then break; fi
  sleep 10
done

echo "== 安装日志尾部 =="
tail -8 /tmp/texlive_min.log

BIN="$TEXDIR/bin/x86_64-linux"
if [ ! -x "$BIN/pdflatex" ]; then
  BIN=$(dirname "$(find "$TEXDIR" -name pdflatex -type f 2>/dev/null | head -1)")
fi
echo "BIN=$BIN"

if [ -x "$BIN/pdflatex" ]; then
  echo "== 补装论文所需包 =="
  "$BIN/tlmgr" install collection-latexrecommended collection-publishers booktabs xcolor --repository "$MIRROR" 2>&1 | tail -6
  echo ""
  "$BIN/pdflatex" --version | head -1
  "$BIN/kpsewhich" IEEEtran.cls || echo "!! 无 IEEEtran"
else
  echo "!! pdflatex 仍不可用（见日志）"
fi
echo "=== MIN2 DONE ==="
