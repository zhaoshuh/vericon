#!/usr/bin/env bash
# 严格检查构建工具链；缺失则给出安装命令（不自动安装）
echo "== toolchain check =="
MISSING=0
for t in cmake gcc g++ make; do
  if command -v "$t" >/dev/null 2>&1; then
    echo "  $t: OK -> $(command -v "$t")"
  else
    echo "  $t: MISSING"
    MISSING=1
  fi
done
echo "== apt availability =="
if command -v apt-get >/dev/null 2>&1; then echo "  apt-get: OK"; else echo "  apt-get: MISSING"; fi
echo "== conda availability =="
if [ -x "$HOME/miniconda3/bin/conda" ]; then
  echo "  conda: OK ($($HOME/miniconda3/bin/conda --version))"
else
  echo "  conda: MISSING"
fi
echo "MISSING=$MISSING"
