#!/usr/bin/env bash
# 为 S6 准备 WSL 编译工具链：apt 优先，conda-forge 兜底
set -uo pipefail

if command -v cmake >/dev/null 2>&1 && command -v g++ >/dev/null 2>&1; then
  echo "ALREADY OK"; exit 0
fi

if sudo -n true 2>/dev/null; then
  echo "== apt install (timeout 600s) =="
  if timeout 600 sudo apt-get update -y >/tmp/apt_update.log 2>&1 \
     && timeout 900 sudo apt-get install -y build-essential cmake >/tmp/apt_install.log 2>&1; then
    echo "APT_OK"; exit 0
  fi
  echo "APT_FAILED (见 /tmp/apt_update.log, /tmp/apt_install.log)"
else
  echo "SUDO_NEEDS_PASSWORD → 跳过 apt"
fi

echo "== conda-forge fallback =="
if "$HOME/miniconda3/bin/conda" install -y -n agentops-py311 -c conda-forge \
      cmake make gcc_linux-64 gxx_linux-64 >/tmp/conda_build_tools.log 2>&1; then
  echo "CONDA_OK"
else
  echo "CONDA_FAILED (见 /tmp/conda_build_tools.log)"
fi
