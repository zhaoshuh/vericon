#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SCOOT 三条人工约束在 vLLM v0.30.0 上的显式漂移测试（S4 轨道A 特例）"""
import json
import os

os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from vllm.config import SchedulerConfig, CacheConfig, ModelConfig, VllmConfig  # noqa

TINY = "/mnt/f/文献/AgentOps/代码/third_party/models/tiny-random-llama"
OUT = "/mnt/f/文献/AgentOps/实验记录/S4验证/scoot-drift.json"


def run(name, fn):
    try:
        fn()
        return {"test": name, "status": "no_error", "detail": "构造成功（引擎未报错）"}
    except Exception as e:
        return {"test": name, "status": "error", "detail": f"{type(e).__name__}: {str(e)[:260]}"}


results = []
base = dict(max_model_len=4096, is_encoder_decoder=False)

# ── SCOOT #1: max_num_batched_tokens >= max_num_seqs ──
results.append(run("SCOOT#1 违反: mtib(256) < mns(512)",
                   lambda: SchedulerConfig(max_num_seqs=512, max_num_batched_tokens=256, **base)))
results.append(run("SCOOT#1 对照: mtib(4096) >= mns(128)",
                   lambda: SchedulerConfig(max_num_seqs=128, max_num_batched_tokens=4096, **base)))

# ── SCOOT #2: enable-chunked-prefill 与 enable-prefix-caching 不能同为 True（0.4.2/0.5.5）──
sc = cc = mc = None
r2a = run("SCOOT#2 构造 SchedulerConfig(chunked=True)",
          lambda: SchedulerConfig(enable_chunked_prefill=True, **base))
r2b = run("SCOOT#2 构造 CacheConfig(prefix=True)",
          lambda: CacheConfig(enable_prefix_caching=True, kv_cache_dtype_skip_layers=[]))
try:
    sc = SchedulerConfig(enable_chunked_prefill=True, **base)
    cc = CacheConfig(enable_prefix_caching=True, kv_cache_dtype_skip_layers=[])
    mc = ModelConfig(model=TINY)
    VllmConfig(model_config=mc, scheduler_config=sc, cache_config=cc)
    r2c = {"test": "SCOOT#2 组合: chunked=True 且 prefix=True 同时装入 VllmConfig",
           "status": "no_error", "detail": "组合构造成功 → 两特性在 v0.30.0 可共存（旧约束已失效）"}
except Exception as e:
    r2c = {"test": "SCOOT#2 组合: chunked=True 且 prefix=True 同时装入 VllmConfig",
           "status": "error", "detail": f"{type(e).__name__}: {str(e)[:260]}"}
results += [r2a, r2b, r2c]

# ── SCOOT #3: 未开 chunked prefill 时 mtib >= max_model_len ──
results.append(run("SCOOT#3 违反: chunked=False 且 mtib(默认 2048) < max_model_len(4096)",
                   lambda: SchedulerConfig(enable_chunked_prefill=False, **base)))
results.append(run("SCOOT#3 对照: chunked=False 且 mtib(4096) >= max_model_len(4096)",
                   lambda: SchedulerConfig(enable_chunked_prefill=False, max_num_batched_tokens=4096, **base)))

verdict = {
    "SCOOT#1": "仍成立（v0.30.0 有同等校验；见 scheduler.py:309）",
    "SCOOT#2": "已失效（两特性可共存；v0.30.0 中不存在此互斥校验）" if r2c["status"] == "no_error" else "需人工复核",
    "SCOOT#3": "仍成立但语义条件化（仅在 chunked_prefill=False 时约束；见 scheduler.py:296-300 / arg_utils.py:2944）",
}
doc = {
    "engine": "vllm-0.30.0",
    "scoot_source": "SCOOT 附录 A.2（vLLM-0.4.2/0.5.5 的人工约束）",
    "tests": results,
    "verdict": verdict,
    "note": "本测试是 Paper 2（版本漂移）的直接素材：人工约束会随版本失效或改变语义。",
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=2)
print(json.dumps(doc, ensure_ascii=False, indent=2)[:2600])
