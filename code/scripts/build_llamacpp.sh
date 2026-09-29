#!/usr/bin/env bash
# 构建 llama.cpp（CPU，-j2 以避让正在运行的 S5 扫描）
set -euo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"

REPO="/mnt/f/文献/AgentOps/代码/third_party/llama.cpp"
cd "$REPO"

# 若使用 conda-forge 编译器，显式指定
if [ -x "$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-gcc" ]; then
  export CC="$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-gcc"
  export CXX="$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-g++"
  echo "using conda compilers: $CC"
fi

cmake -B build -DGGML_CUDA=OFF -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON
cmake --build build -j2 --target llama-cli llama-server

echo "== build done =="
ls -la build/bin/ | head -20
