#!/usr/bin/env bash
# 安装最小 TeX Live 用于本地编译验证（IEEEtran 在 texlive-publishers）
set -uo pipefail
if sudo -n true 2>/dev/null; then
  echo "sudo 可用"
  sudo apt-get update -qq
  DEBIAN_FRONTEND=noninteractive sudo apt-get install -y -qq \
    texlive-latex-base texlive-latex-recommended texlive-publishers texlive-fonts-recommended
  echo "=== texlive 安装完成 ==="
  which pdflatex && pdflatex --version | head -2
else
  echo "无免密 sudo，放弃本地安装（改用 Overleaf 编译）"
fi
