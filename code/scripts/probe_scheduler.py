#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定位 SchedulerConfig 基线失败原因（复用 verifier 的 build_kwargs）。"""
import importlib.util
import json
import os
import sys

os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

spec = importlib.util.spec_from_file_location("v", "/mnt/f/文献/AgentOps/代码/scripts/s4_verify_vllm.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
v.IDX = v.param_index()

cls = v.import_class("SchedulerConfig", "vllm/config/scheduler.py")
print("cls:", cls)

for assign in (None, {}, {"enable_chunked_prefill": False, "max_model_len": 4096},
               {"max_num_batched_tokens": 256, "max_num_seqs": 512}):
    kw, prob = v.build_kwargs(cls, "SchedulerConfig", assign or {})
    print("\n---- assign:", assign)
    print("problem:", prob)
    if kw is None:
        continue
    short = {k: (repr(val)[:60]) for k, val in kw.items()}
    print("kwargs:", json.dumps(short, ensure_ascii=False, indent=1)[:1200])
    try:
        cls(**kw)
        print("=> OK")
    except Exception as e:
        print("=> FAIL:", type(e).__name__)
        print(str(e)[:1200])
