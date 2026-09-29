#!/usr/bin/env bash
# ⚠️ 已弃用：本脚本建的是 Python 3.14 环境，Vidur 与其不兼容
#    （argparse.BooleanOptionalAction 在 3.13+ 不接受 type 参数）。
#    请改用 scripts/setup_env_miniconda.sh（Python 3.11 + 锁定版本）。
#    保留本文件是为了记录这次失败（见 实验记录/runs.jsonl 中 status=failed 的记录）。
#
# S2 环境安装脚本（WSL Ubuntu 侧）
# 用法: bash /mnt/f/文献/AgentOps/代码/scripts/setup_env_wsl.sh
set -uo pipefail

VENV="$HOME/.venvs/agentops"
REPO="/mnt/f/文献/AgentOps/代码/third_party/vidur"
PYPI_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"

echo "== 1. 安装 uv（用于创建 venv，避免系统 python3.14-venv 缺失） =="
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
uv --version

echo "== 2. 创建 venv（复用系统 Python 3.14） =="
# 说明：Vidur 要求 python>=3.10；本机 WSL 只有 3.14。
# 先用 3.14 尝试，若依赖安装/运行失败则回退 Miniconda(python=3.11)，见 README。
# 不加 --seed：不需要 venv 内的 pip，直接用 uv pip 装包，避免卡在 PyPI 下载。
uv venv --python /usr/bin/python3 --clear "$VENV"
source "$VENV/bin/activate"
python -V
export UV_INDEX_URL="$PYPI_MIRROR"   # 之后所有 uv pip 都走镜像

echo "== 3. 安装核心依赖 =="
uv pip install numpy pandas scikit-learn matplotlib seaborn ddsketch fasteners wandb plotly_express kaleido optuna

echo "== 4. 安装 Vidur（普通安装；运行时以仓库源码为准，见 vidur_backend._ensure_vidur_on_path） =="
uv pip install --no-deps "$REPO"

echo "== 5. 验证导入 =="
cd "/mnt/f/文献/AgentOps/代码"
python - <<'PY'
import sys
from agentops.paths import vidur_dir

# 与运行时一致：把 Vidur 仓库根加入 sys.path（不依赖 editable 安装）
sys.path.insert(0, str(vidur_dir()))

import vidur  # noqa: E402
import numpy, pandas, sklearn, optuna, plotly_express, wandb  # noqa: E402

print("PYTHON", sys.version.split()[0])
print("Vidur 源码:", vidur.__file__)
for m in (numpy, pandas, sklearn, optuna, plotly_express, wandb):
    print(f"OK {m.__name__}=={getattr(m, '__version__', 'n/a')}")
PY
echo "SETUP_DONE"
