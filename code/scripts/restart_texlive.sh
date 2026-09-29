#!/usr/bin/env bash
# 重启 TeX Live 安装（清掉卡死的进程与临时目录）
set -uo pipefail
echo "== 杀掉卡死的安装进程 =="
pkill -f install-tl 2>/dev/null || true
pkill -f "archive/.*tar.xz" 2>/dev/null || true
sleep 2
rm -rf /tmp/M2* 2>/dev/null || true
echo "已清理"

echo "== 重启安装（TUNA 镜像） =="
MIRROR="https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/tlnet"
TEXDIR="$HOME/texlive/2026"
cd /tmp/install-tl-*/
setsid nohup ./install-tl -profile tl.profile -repository "$MIRROR" -no-interaction > /tmp/texlive_install.log 2>&1 &
echo "launched pid=$!"
sleep 15
echo "---- 15 秒后：下载目录大小 ----"
du -sh /tmp/M2* 2>/dev/null | tail -3
tail -5 /tmp/texlive_install.log 2>/dev/null
