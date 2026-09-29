#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S4 第二轮探针：找出 SpeculativeConfig/CompilationConfig/VllmConfig 基线失败原因。"""
import dataclasses
import os

os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from vllm.config import SpeculativeConfig, CompilationConfig, VllmConfig, ModelConfig  # noqa


def unwrap(f):
    d = f.default
    if isinstance(d, FieldInfo):
        dv = getattr(d, "default", PydanticUndefined)
        if dv is not PydanticUndefined:
            return ("value", dv)
        df = getattr(d, "default_factory", None)
        if df is not None:
            return ("factory", df)
        return ("required", None)
    if d is dataclasses.MISSING:
        df = getattr(f, "default_factory", dataclasses.MISSING)
        if df is not dataclasses.MISSING:
            return ("factory", df)
        return ("required", None)
    return ("value", d)


for cls in (SpeculativeConfig, CompilationConfig):
    print("=" * 20, cls.__name__, "=" * 20)
    for f in dataclasses.fields(cls):
        kind, v = unwrap(f)
        info = f"{kind}={repr(v)[:60]}"
        print(f"  {f.name}: init={getattr(f, 'init', True)} {info}")
    kw = {}
    for f in dataclasses.fields(cls):
        if not getattr(f, "init", True):
            continue
        kind, v = unwrap(f)
        if kind == "value":
            kw[f.name] = v
        elif kind == "factory":
            try:
                kw[f.name] = v()
            except Exception:
                pass
    try:
        cls(**kw)
        print("  baseline -> OK")
    except Exception as e:
        print("  baseline -> FAIL:")
        print("   ", type(e).__name__, str(e)[:900])

print("=" * 20, "ModelConfig 字段概览", "=" * 20)
for f in dataclasses.fields(ModelConfig):
    kind, v = unwrap(f)
    if kind == "required" or f.name in ("model", "tokenizer", "hf_config", "hf_text_config"):
        print(f"  {f.name}: {kind} {repr(v)[:60]}")

# 本地 tiny 模型是否就绪？
local_model = os.environ.get("S4_TINY_MODEL", "/mnt/f/文献/AgentOps/代码/third_party/models/tiny-random-llama")
print("local tiny model exists:", os.path.isdir(local_model), local_model)
if os.path.isdir(local_model):
    try:
        mc = ModelConfig(model=local_model)
        print("ModelConfig(local tiny) -> OK")
    except Exception as e:
        print("ModelConfig(local tiny) -> FAIL:", type(e).__name__, str(e)[:400])
