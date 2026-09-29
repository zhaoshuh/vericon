#!/usr/bin/env bash
# 精简安装：scheme-basic + 按需补包（IEEEtran 等），大幅缩短时间
set -uo pipefail
MIRROR="https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/tlnet"
TEXDIR="$HOME/texlive/2026"

echo "== 停掉当前（medium）安装 =="
pkill -f install-tl 2>/dev/null || true
pkill -f "archive/.*tar" 2>/dev/null || true
sleep 2
rm -rf "$TEXDIR" /tmp/M2* 2>/dev/null || true
echo "已清理"

cd /tmp/install-tl-*/
cat > tl-min.profile <<EOF
selected_scheme scheme-basic
TEXDIR $TEXDIR
instopt_adjustpath 0
instopt_adjustrepo 0
tlpdbopt_autobackup 0
EOF

echo "== 安装 scheme-basic（TUNA） =="
setsid nohup ./install-tl -profile tl-min.profile -repository "$MIRROR" -no-interaction > /tmp/texlive_min.log 2>&1 &
PID=$!
echo "pid=$PID"

# 等待安装完成（轮询进程）
for i in $(seq 1 60); do
  if ! kill -0 "$PID" 2>/dev/null; then break; fi
  sleep 10
done

echo "== 安装输出尾部 =="
tail -6 /tmp/texlive_min.log

BIN="$TEXDIR/bin/x86_64-linux"
if [ ! -x "$BIN/pdflatex" ]; then
  echo "!! pdflatex 不在预期路径，搜索中..."
  find "$TEXDIR" -name pdflatex -type f 2>/dev/null | head -3
  BIN=$(dirname "$(find "$TEXDIR" -name pdflatex -type f 2>/dev/null | head -1)")
fi
echo "BIN=$BIN"

echo "== 补装论文所需包 =="
"$BIN/tlmgr" install collection-latexrecommended collection-publishers booktabs xcolor --repository "$MIRROR" 2>&1 | tail -8

echo ""
echo "== 验证 =="
"$BIN/pdflatex" --version 2>/dev/null | head -1
"$BIN/kpsewhich" IEEEtran.cls 2>/dev/null || echo "!! 无 IEEEtran"
echo "=== TEXLIVE MIN INSTALL DONE ==="
