#!/usr/bin/env bash
# 用 Python 3.11 + 锁定版本重建环境（Vidur 是 2024 年代码，需要旧版依赖）
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
VENV="$HOME/.venvs/agentops311"
REPO="/mnt/f/文献/AgentOps/代码/third_party/vidur"
PYPI_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"

echo "== 1. 准备 Python 3.11 =="
if [ -x "$VENV/bin/python" ] && "$VENV/bin/python" -c "import sys; assert sys.version_info[:2]==(3,11)" 2>/dev/null; then
  echo "已存在可用 venv: $VENV"
else
  export UV_PYTHON_INSTALL_MIRROR="https://mirrors.tuna.tsinghua.edu.cn/github-release/astral-sh/python-build-standalone"
  if ! uv python install 3.11; then
    echo "!! uv 镜像下载 Python 3.11 失败，改用 Miniconda 方案（见 README）"
    exit 2
  fi
  uv venv --python 3.11 --clear "$VENV" || exit 3
fi
source "$VENV/bin/activate"
python -V || exit 4
export UV_INDEX_URL="$PYPI_MIRROR"

echo "== 2. 安装锁定版本依赖（对齐 Vidur 的依赖年代：numpy<2 / pandas<2.2 / sklearn<1.5） =="
uv pip install \
  "numpy>=1.24,<2" "pandas>=2.0,<2.2" "scikit-learn>=1.3,<1.5" \
  matplotlib seaborn plotly plotly_express kaleido ddsketch fasteners wandb optuna || exit 5

echo "== 3. 验证 =="
cd "/mnt/f/文献/AgentOps/代码"
python - <<'PY' || exit 6
import sys
from agentops.paths import vidur_dir
sys.path.insert(0, str(vidur_dir()))
import vidur, numpy, pandas, sklearn, optuna
print("PYTHON", sys.version.split()[0])
print("Vidur:", vidur.__file__)
print("numpy", numpy.__version__, "| pandas", pandas.__version__,
      "| sklearn", sklearn.__version__, "| optuna", optuna.__version__)
PY
echo "SETUP311_DONE"
