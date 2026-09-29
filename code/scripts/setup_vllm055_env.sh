#!/usr/bin/env bash
# P2 执行级：vLLM 0.5.5 独立环境（用于 SCOOT 规则在原始锚点版本的执行复核）
set -e
VENV="$HOME/.venvs/vllm-055"
BASE="$HOME/.venvs/agentops-py311/bin/python"

if [ ! -x "$VENV/bin/python" ]; then
  echo "== create venv =="
  "$BASE" -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install -U pip -q
pip install -q uv
echo "== install vllm==0.5.5 =="
uv pip install --python "$VENV/bin/python" "vllm==0.5.5" \
  --index-url https://pypi.tuna.tsinghua.edu.cn/simple
echo "=== install done ==="
"$VENV/bin/python" -c "import vllm; print('vllm', vllm.__version__)"
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
