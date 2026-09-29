#!/usr/bin/env bash
# 修复 vLLM 0.5.5 环境的传递依赖版本（解析器装了过新版本）
set -uo pipefail
VENV="$HOME/.venvs/vllm-055"

echo "== pin era-correct deps =="
"$VENV/bin/python" -m uv pip install --python "$VENV/bin/python" \
  "datasets==2.19.2" "pyarrow==16.1.0" "transformers==4.42.5" "tokenizers==0.19.1" \
  --index-url https://pypi.tuna.tsinghua.edu.cn/simple

echo "== import probe =="
"$VENV/bin/python" - <<'PY'
import traceback
try:
    import vllm
    print("vllm:", vllm.__version__)
except Exception:
    traceback.print_exc()
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
