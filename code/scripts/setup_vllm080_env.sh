#!/usr/bin/env bash
# P2 执行级第三个点：vLLM 0.8.0 独立环境（仅用于配置校验路径执行）
set -uo pipefail
VENV="$HOME/.venvs/vllm-080"
BASE="$HOME/.venvs/agentops-py311/bin/python"

if [ ! -x "$VENV/bin/python" ]; then
  echo "== create venv =="
  "$BASE" -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install -U pip -q
pip install -q uv

echo "== install vllm==0.8.0 =="
"$VENV/bin/python" -m uv pip install --python "$VENV/bin/python" "vllm==0.8.0" \
  --index-url https://pypi.tuna.tsinghua.edu.cn/simple

echo "== import probe =="
"$VENV/bin/python" - <<'PY'
import traceback
try:
    import vllm
    print("vllm:", vllm.__version__)
except Exception:
    traceback.print_exc()
for stmt in ("from vllm.config import SchedulerConfig, CacheConfig",
             "from vllm.engine.arg_utils import EngineArgs"):
    try:
        exec(stmt)
        print("OK:", stmt)
    except Exception:
        traceback.print_exc()
PY
echo "=== vllm-080 setup done ==="
