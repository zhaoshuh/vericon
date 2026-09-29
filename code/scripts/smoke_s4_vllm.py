#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S4 轨道A 冒烟测试：确认 vllm 配置校验路径可离线使用，并验证旗舰约束。

跑法（WSL）：bash /mnt/f/文献/AgentOps/代码/scripts/run_smoke_s4.sh
"""
import dataclasses
import traceback

print("#### import 检查 ####")
import vllm
print("vllm:", vllm.__version__)

from vllm.config import SchedulerConfig, CacheConfig, ParallelConfig  # noqa
print("config imports OK")

print("\n#### SchedulerConfig 字段（默认值） ####")
for f in dataclasses.fields(SchedulerConfig):
    d = repr(f.default)
    if len(d) > 80:
        d = d[:80] + "..."
    print(f"  {f.name} = {d}")

print("\n#### 冒烟1：违反 max_num_batched_tokens >= max_num_seqs（构造期应报错） ####")
try:
    SchedulerConfig(max_num_seqs=512, max_num_batched_tokens=256)
    print("  结果: 未报错（意外！需检查）")
except Exception as e:
    print(f"  结果: {type(e).__name__}: {str(e)[:300]}")

print("\n#### 冒烟2：合法配置（不应报错） ####")
try:
    cfg = SchedulerConfig(max_num_seqs=128, max_num_batched_tokens=4096)
    print("  结果: 构造成功（合法配置，符合预期）")
except Exception as e:
    print(f"  结果: {type(e).__name__}: {str(e)[:300]}")

print("\n#### 冒烟3：engine_args 层（不调 create_engine_config） ####")
try:
    from vllm.engine.arg_utils import EngineArgs
    EngineArgs(model="Qwen/Qwen2.5-0.5B", max_num_seqs=512, max_num_batched_tokens=256)
    print("  EngineArgs 未报错（检查可能在 create_engine_config 阶段）")
except Exception as e:
    print(f"  EngineArgs: {type(e).__name__}: {str(e)[:300]}")

print("\n冒烟测试结束")
