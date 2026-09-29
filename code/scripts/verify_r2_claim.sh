#!/usr/bin/env bash
for V in v0.4.2 v0.5.5 v0.6.6 v0.8.0; do
  ROOT="/mnt/f/文献/AgentOps/代码/third_party/vllm-versions/$V"
  [ -d "$ROOT" ] || continue
  echo "================= $V ================="
  grep -rn "chunked prefill cannot be used\|prefix_cache_hit\|chunked_prefill_enabled" "$ROOT/vllm/worker/model_runner.py" 2>/dev/null | head -12
  echo "---- 全树搜索报错消息 ----"
  grep -rn "cannot be used with prefix caching" "$ROOT/vllm" 2>/dev/null | head -5
done
