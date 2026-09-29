#!/usr/bin/env bash
# 经清华镜像安装 TeX Live（用户级，无需 sudo）用于本地编译验证
set -uo pipefail
MIRROR="https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/tlnet"
TEXDIR="$HOME/texlive/2026"

cd /tmp
echo "== 下载 install-tl =="
curl -sL -o install-tl-unx.tar.gz "$MIRROR/install-tl-unx.tar.gz" || { echo "!! 下载失败"; exit 1; }
tar xzf install-tl-unx.tar.gz
cd install-tl-*/

echo "== 写安装 profile（scheme-medium） =="
cat > tl.profile <<EOF
selected_scheme scheme-medium
TEXDIR $TEXDIR
TEXMFHOME \$TEXDIR/texmf
TEXMFLOCAL \$TEXDIR/texmf-local
TEXMFSYSCONFIG \$TEXDIR/texmf-config
TEXMFSYSVAR \$TEXDIR/texmf-var
TEXMFVAR \$TEXDIR/texmf-var
TEXMFCONFIG \$TEXDIR/texmf-config
instopt_adjustpath 0
instopt_adjustrepo 0
tlpdbopt_autobackup 0
EOF

echo "== 安装（清华镜像） =="
./install-tl -profile tl.profile -repository "$MIRROR" -no-interaction 2>&1 | tail -25

echo ""
echo "=== TEXLIVE INSTALL DONE ==="
BIN="$TEXDIR/bin/x86_64-linux"
"$BIN/pdflatex" --version 2>/dev/null | head -1 || echo "!! pdflatex 不可用"
echo "IEEEtran.cls: $(find "$TEXDIR" -name 'IEEEtran.cls' 2>/dev/null | head -1 || echo '未找到')"
