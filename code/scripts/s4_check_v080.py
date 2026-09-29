#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2 执行级：在 vLLM 0.8.0 上复核 SCOOT 三条规则
输出：/mnt/f/文献/AgentOps/实验记录/P2-版本研究/v0.8.0-exec.json
"""
import json
import os
import traceback
from datetime import datetime, timezone

os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")
OUT = "/mnt/f/文献/AgentOps/实验记录/P2-版本研究/v0.8.0-exec.json"

results = []


def run(name, fn):
    try:
        fn()
        results.append({"case": name, "status": "no_error", "detail": "构造成功（未报错）"})
    except Exception as e:
        results.append({"case": name, "status": "error",
                        "detail": f"{type(e).__name__}: {str(e)[:300]}"})


print("### import 检查 ###")
try:
    import vllm  # noqa: E402
    print("vllm:", vllm.__version__)
except Exception as e:
    print("full import vllm 失败：", type(e).__name__)

from vllm.config import SchedulerConfig, CacheConfig  # noqa: E402
print("config imports OK")

import inspect  # noqa: E402
try:
    print("SchedulerConfig.__init__:", str(inspect.signature(SchedulerConfig.__init__))[:420])
except Exception as e:
    print("sig error:", e)

# R1（隔离用例：max_model_len 调小，避免 R3 抢先触发）
run("R1 违反: mtib(2048) < mns(4096)（max_model_len=2048 使 R3 通过）",
    lambda: SchedulerConfig(max_num_seqs=4096, max_num_batched_tokens=2048, max_model_len=2048))
run("R1 对照: mtib(4096) >= mns(128)",
    lambda: SchedulerConfig(max_num_seqs=128, max_num_batched_tokens=4096, max_model_len=4096))

# R2：chunked ⊥ prefix 是否被强制
run("R2a: SchedulerConfig(chunked=True)",
    lambda: SchedulerConfig(max_num_seqs=128, max_num_batched_tokens=4096,
                            max_model_len=4096, enable_chunked_prefill=True))
run("R2b: CacheConfig(prefix=True)",
    lambda: CacheConfig(block_size=16, gpu_memory_utilization=0.9, swap_space=4,
                        cache_dtype="auto", enable_prefix_caching=True))
try:
    from vllm.engine.arg_utils import EngineArgs  # noqa: E402
    TINY = "/mnt/f/文献/AgentOps/代码/third_party/models/tiny-random-llama"
    run("R2c: EngineArgs(chunked=True, prefix=True) 构造",
        lambda: EngineArgs(model=TINY, enable_chunked_prefill=True, enable_prefix_caching=True,
                           max_num_seqs=128, max_num_batched_tokens=4096))
except Exception as e:
    print("EngineArgs import failed:", e)

# R3
run("R3 违反: chunked=False 且 mtib(2048) < max_model_len(4096)",
    lambda: SchedulerConfig(max_num_seqs=128, max_num_batched_tokens=2048,
                            max_model_len=4096, enable_chunked_prefill=False))
run("R3 对照: chunked=False 且 mtib(4096) >= max_model_len(4096)",
    lambda: SchedulerConfig(max_num_seqs=128, max_num_batched_tokens=4096,
                            max_model_len=4096, enable_chunked_prefill=False))

doc = {
    "engine": "vllm-0.8.0（中间版本执行点）",
    "method": "构造违反配置 → 真实配置校验路径 → 捕获报错",
    "results": results,
    "generated_at": datetime.now(timezone.utc).isoformat(),
}
json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(doc, ensure_ascii=False, indent=2)[:2000])
print("->", OUT)
