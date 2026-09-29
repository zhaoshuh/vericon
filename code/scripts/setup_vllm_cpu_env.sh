#!/usr/bin/env bash
# S4 轨道 A：vLLM 真实引擎配置校验环境（独立 venv，不污染 S2 的 Vidur 环境）
set -e

VENV="$HOME/.venvs/vllm-cpu"
BASE_PY="$HOME/.venvs/agentops-py311/bin/python"

echo "== base python =="
"$BASE_PY" --version

if [ ! -x "$VENV/bin/python" ]; then
  echo "== create venv =="
  "$BASE_PY" -m venv "$VENV"
fi

source "$VENV/bin/activate"
pip install -U pip -q
pip install -q uv

echo "== install vllm==0.30.0 (tsinghua mirror) =="
uv pip install --python "$VENV/bin/python" "vllm==0.30.0" \
  --index-url https://pypi.tuna.tsinghua.edu.cn/simple

echo "=== install done ==="
"$VENV/bin/python" -c "import vllm; print('vllm version:', vllm.__version__)"

echo "== config import probe =="
"$VENV/bin/python" - <<'PY'
import traceback
try:
    from vllm.config import SchedulerConfig, CacheConfig
    print("config import OK")
except Exception:
    traceback.print_exc()
try:
    from vllm.engine.arg_utils import EngineArgs
    print("EngineArgs import OK")
except Exception:
    traceback.print_exc()
PY