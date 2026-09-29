#!/usr/bin/env bash
# 下载 tectonic（免安装 LaTeX 引擎）并编译验证 TSE 稿件
set -uo pipefail
mkdir -p "$HOME/bin"
cd /tmp

if [ ! -x "$HOME/bin/tectonic" ]; then
  echo "== 下载 tectonic 0.17.0 (linux-musl) =="
  curl -sL -o tectonic.tar.gz "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-unknown-linux-musl.tar.gz"
  tar xzf tectonic.tar.gz -C "$HOME/bin"
fi
echo "tectonic: $("$HOME/bin/tectonic" --version 2>&1 | head -1)"

echo "== 编译 main.tex（首次会拉取 TeX 宏包，约 1-3 分钟） =="
cd "/mnt/f/文献/AgentOps/论文/latex"
"$HOME/bin/tectonic" main.tex --keep-logs 2>&1 | tail -45
echo ""
echo "== 产物 =="
ls -la main.pdf 2>/dev/null || echo "!! 无 main.pdf"
