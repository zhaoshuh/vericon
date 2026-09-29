#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S4 冒烟2：补齐必填字段后验证旗舰约束；盘点各 Config 类的必填字段。"""
import dataclasses
import pydantic

from vllm.config import SchedulerConfig, CacheConfig, ParallelConfig, ModelConfig, CompilationConfig  # noqa

print("#### 各 Config 类必填字段盘点 ####")
for cls in [SchedulerConfig, CacheConfig, ParallelConfig, ModelConfig, CompilationConfig]:
    try:
        req = []
        opt = 0
        for f in dataclasses.fields(cls):
            if f.default is dataclasses.MISSING:
                req.append(f.name)
            else:
                opt += 1
        print(f"{cls.__name__}: required={req} optional={opt}")
    except Exception as e:
        print(f"{cls.__name__}: fields error {e}")

print("\n#### 旗舰约束：max_num_batched_tokens >= max_num_seqs ####")
base = dict(max_model_len=4096, is_encoder_decoder=False)
try:
    SchedulerConfig(max_num_seqs=128, max_num_batched_tokens=4096, **base)
    print("baseline: OK（合法配置构造成功）")
except Exception as e:
    print(f"baseline: FAIL {type(e).__name__}: {str(e)[:400]}")

try:
    SchedulerConfig(max_num_seqs=512, max_num_batched_tokens=256, **base)
    print("violation: NO ERROR（意外，约束可能不在此路径）")
except Exception as e:
    print(f"violation: {type(e).__name__}")
    print(f"   {str(e)[:400]}")

print("\n#### 测试 create_engine_config 是否可离线跑（EngineArgs 全链路） ####")
try:
    from vllm.engine.arg_utils import EngineArgs
    ea = EngineArgs(model="Qwen/Qwen2.5-0.5B", max_num_seqs=512, max_num_batched_tokens=256)
    try:
        cfg = ea.create_engine_config()
        print("create_engine_config: 成功（无 GPU 也能构造！）")
    except Exception as e:
        print(f"create_engine_config: {type(e).__name__}: {str(e)[:300]}")
except Exception as e:
    print("EngineArgs: 构造失败", type(e).__name__, str(e)[:300])
