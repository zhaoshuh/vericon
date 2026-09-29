#!/usr/bin/env bash
# P2 执行级第三个点：vLLM 0.8.0（修复版：xgrammar 从 PyPI 直装，其余走镜像）
set -uo pipefail
VENV="$HOME/.venvs/vllm-080"
MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"

echo "== step1: xgrammar 从 PyPI 直装 =="
"$VENV/bin/python" -m uv pip install --python "$VENV/bin/python" "xgrammar==0.1.16" \
  --index-url https://pypi.org/simple || \
"$VENV/bin/python" -m uv pip install --python "$VENV/bin/python" "xgrammar==0.1.16" \
  --index-url https://pypi.org/simple --trusted-host pypi.org || echo "!! xgrammar direct failed"

echo "== step2: vllm==0.8.0（镜像） =="
"$VENV/bin/python" -m uv pip install --python "$VENV/bin/python" "vllm==0.8.0" \
  --index-url "$MIRROR" || echo "!! vllm install failed"

echo "== step3: 若 vllm 仍失败，退回 0.8.2 =="
"$VENV/bin/python" -c "import vllm" 2>/dev/null || \
"$VENV/bin/python" -m uv pip install --python "$VENV/bin/python" "vllm==0.8.2" \
  --index-url "$MIRROR" || echo "!! fallback also failed"

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
echo "=== vllm-080 setup v2 done ==="
