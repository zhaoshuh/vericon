#!/usr/bin/env bash
# 用 Miniconda 建 Python 3.11 环境（对齐 Vidur 的年代），
# pip 走清华镜像，依赖版本锁定。
set -uo pipefail
MC="$HOME/miniconda3"
PREFIX="$HOME/.venvs/agentops-py311"
PYPI="https://pypi.tuna.tsinghua.edu.cn/simple"

echo "== 1. 安装 Miniconda（若未安装） =="
if [ ! -x "$MC/bin/conda" ]; then
  curl -fsSL -o /tmp/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh || exit 1
  bash /tmp/miniconda.sh -b -p "$MC" || exit 2
fi
"$MC/bin/conda" --version

echo "== 2. 创建 Python 3.11 环境 =="
source "$MC/etc/profile.d/conda.sh"
if [ ! -x "$PREFIX/bin/python" ]; then
  conda create -y -p "$PREFIX" python=3.11 || exit 3
fi
conda activate "$PREFIX"
python -V || exit 4

echo "== 3. pip 安装锁定版本依赖 =="
python -m pip install -q -i "$PYPI" -U pip || exit 5
python -m pip install -i "$PYPI" \
  "numpy>=1.24,<2" "pandas>=2.0,<2.2" "scikit-learn>=1.3,<1.5" \
  matplotlib seaborn plotly plotly_express kaleido ddsketch fasteners wandb optuna || exit 6

echo "== 4. 创建 WSL 本地 Vidur 快照（提速：drvfs 下导入 57s → 本地 ~13s） =="
FAST="$HOME/vidur-fast"
mkdir -p "$FAST"
cp -r "$REPO/vidur" "$FAST/" 2>/dev/null || true
ln -sfn "$REPO/data" "$FAST/data"
ls "$FAST"

echo "== 5. 验证 =="
cd "/mnt/f/文献/AgentOps/代码" || exit 7
python - <<'PY' || exit 8
import sys
from agentops.paths import vidur_dir
sys.path.insert(0, str(vidur_dir()))
import vidur, numpy, pandas, sklearn, optuna
print("PYTHON", sys.version.split()[0])
print("Vidur:", vidur.__file__)
print("numpy", numpy.__version__, "| pandas", pandas.__version__,
      "| sklearn", sklearn.__version__, "| optuna", optuna.__version__)
PY
echo "SETUP_MINICONDA_DONE"
