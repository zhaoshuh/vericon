#!/usr/bin/env bash
# 检查 vidur 包结构 + 真实导入
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
cd "/mnt/f/文献/AgentOps/代码"

echo "--- vidur/__init__.py 是否存在 ---"
ls -la /mnt/f/文献/AgentOps/代码/third_party/vidur/vidur/__init__.py 2>&1
echo "--- 直接导入测试 ---"
python - <<'PY'
import sys
from agentops.paths import vidur_dir
sys.path.insert(0, str(vidur_dir()))
import vidur
print("vidur.__path__ =", list(vidur.__path__))
from vidur.config import SimulationConfig
from vidur.simulator import Simulator
from vidur.utils.random import set_seeds
print("Simulator OK:", Simulator)
PY
