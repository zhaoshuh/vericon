#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S4 · 轨道A v3：在 vLLM 真实配置校验路径上做证伪（构造违反配置 → 期望报错）

v3 改进（基于两轮实测）：
- pydantic FieldInfo 解包；init=False 字段跳过
- 每类"基线补丁"（SpeculativeConfig.num_speculative_tokens 等必填/缺省坑）
- ModelConfig / VllmConfig：使用本地 tiny 模型（/mnt/f/.../models/tiny-random-llama）
- 点号键归一：`eplb_config.num_redundant_experts` → 构造 EPLBConfig 再注入 ParallelConfig
- 基线优先：先证明合法基线可构造，再叠加违反赋值；避免把"缺字段错误"误判为 confirmed

用法（WSL）：~/.venvs/vllm-cpu/bin/python s4_verify_vllm.py [cases.json] [records.jsonl] [--limit N] [--only C003]
"""
import dataclasses
import importlib
import json
import os
import sys
from datetime import datetime, timezone

os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

try:
    from pydantic.fields import FieldInfo
    from pydantic_core import PydanticUndefined
except Exception:  # pragma: no cover
    FieldInfo = ()  # type: ignore[assignment]
    PydanticUndefined = object()

CASES_DEFAULT = "/mnt/f/文献/AgentOps/实验记录/S4验证/cases.json"
REC_DEFAULT = "/mnt/f/文献/AgentOps/实验记录/S4验证/records.jsonl"
PARAMS_PATH = "/mnt/f/文献/AgentOps/实验记录/参数清单.json"
TINY_MODEL = "/mnt/f/文献/AgentOps/代码/third_party/models/tiny-random-llama"

BASE_KWARGS = {
    "SchedulerConfig": {"max_model_len": 4096, "is_encoder_decoder": False},
    "CacheConfig": {"kv_cache_dtype_skip_layers": []},
    "SpeculativeConfig": {"num_speculative_tokens": 5, "method": "ngram", "prompt_lookup_max": 4, "prompt_lookup_min": 2},
    "CompilationConfig": {"cudagraph_capture_sizes": [1, 2, 4, 8]},
    "ModelConfig": {"model": TINY_MODEL},
    "VllmConfig": {"__model_config_instance__": True},
}
GENERIC_FALLBACK = {"max_model_len": 4096, "is_encoder_decoder": False}

# 被 pydantic "before-validator" 消费的虚拟键（不在 dataclasses.fields 里，但构造时可传）
EXTRA_ASSIGN_KEYS = {
    "SchedulerConfig": {"max_model_len", "is_encoder_decoder"},
}

# 顶层配置 → 嵌套配置字段名（用于把子配置字段注入为嵌套对象）
NESTED_FIELD_MAP = {
    "VllmConfig": {
        "ModelConfig": "model_config",
        "CacheConfig": "cache_config",
        "ParallelConfig": "parallel_config",
        "SchedulerConfig": "scheduler_config",
        "DeviceConfig": "device_config",
        "LoadConfig": "load_config",
        "ObservabilityConfig": "observability_config",
        "LoRAConfig": "lora_config",
        "CompilationConfig": "compilation_config",
        "SpeculativeConfig": "speculative_config",
        "MultiModalConfig": "multimodal_config",
        "OffloadConfig": "offload_config",
        "StructuredOutputsConfig": "structured_outputs_config",
        "ProfilerConfig": "profiler_config",
        "KernelConfig": "kernel_config",
        "WatermarkConfig": "watermark_config",
        "EPLBConfig": "eplb_config",
        "EngramConfig": "engram_config",
        "WeightTransferConfig": "weight_transfer_config",
        "TensorizerConfig": "tensorizer_config",
        "ReasoningConfig": "reasoning_config",
        "ECTransferConfig": "ec_transfer_config",
        "KVTransferConfig": "kv_transfer_config",
        "QuantizationConfigArgs": "quantization_config",
    }
}

IDX = {}
_SPECIAL = {}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def param_index():
    data = load_json(PARAMS_PATH)
    idx = {}
    for p in data.get("params", []):
        idx.setdefault(p["name"], []).append(p)
    return idx


def import_class(name, file_hint=None):
    try:
        import vllm.config as vc
        if hasattr(vc, name):
            return getattr(vc, name)
    except Exception:
        pass
    if file_hint:
        rel = file_hint[:-3].replace("/", ".") if file_hint.endswith(".py") else file_hint.replace("/", ".")
        try:
            mod = importlib.import_module(rel)
            if hasattr(mod, name):
                return getattr(mod, name)
        except Exception:
            pass
    return None


def model_config_instance():
    if "mc" not in _SPECIAL:
        MC = import_class("ModelConfig")
        _SPECIAL["mc"] = MC(model=TINY_MODEL)
    return _SPECIAL["mc"]


def class_fields(cls):
    try:
        return {f.name: f for f in dataclasses.fields(cls)}
    except Exception:
        return None


def unwrap_default(f):
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


def base_kwargs(cls_name, fields):
    out = {}
    base = dict(BASE_KWARGS.get(cls_name, {}))
    if base.pop("__model_config_instance__", False):
        if "model_config" in fields:
            try:
                out["model_config"] = model_config_instance()
            except Exception:
                pass
    # 注意：不检查 k in fields —— SchedulerConfig 的虚拟键必须传入
    for k, v in base.items():
        out[k] = v
    return out


def build_nested_multi(holder_cls_name, file_hint, overrides):
    """构造一个子配置对象（多个字段覆盖）"""
    cls = import_class(holder_cls_name, file_hint)
    if cls is None:
        return None, f"类 {holder_cls_name} 不可导入"
    kw, problem = build_kwargs(cls, holder_cls_name, dict(overrides))
    if kw is None:
        return None, problem
    try:
        return cls(**kw), None
    except Exception as ex:
        return None, f"{type(ex).__name__}: {str(ex)[:200]}"


def guess_holder_from_dict(d):
    """根据 dict 的键猜测其所属配置类（用于把嵌套 dict 构造成子配置对象）"""
    if not isinstance(d, dict) or not d:
        return None
    ks = list(d.keys())
    counts = {}
    for k in ks:
        for e in IDX.get(k, []):
            if e["class"] != "EngineArgs":
                counts[e["class"]] = counts.get(e["class"], 0) + 1
    for cls_name, cnt in sorted(counts.items(), key=lambda kv: -kv[1]):
        if cnt >= max(1, len(ks) // 2):
            fh = None
            for k in ks:
                for e in IDX.get(k, []):
                    if e["class"] == cls_name:
                        fh = e.get("file")
                        break
                if fh:
                    break
            return cls_name, fh
    return None


def build_kwargs(cls, cls_name, assign):
    """默认值 + 基线补丁 + 违反赋值（支持点号嵌套）；返回 (kwargs, problem)"""
    fields = class_fields(cls)
    if fields is None:
        return None, "非 dataclass，无法构造"

    kw = {}
    missing = []
    for name, f in fields.items():
        d = f.default
        init_flag = getattr(f, "init", True)
        if isinstance(d, FieldInfo):
            init_flag = init_flag and getattr(d, "init", True)
        if not init_flag:
            continue  # init=False（含 FieldInfo 内标记）字段不能/无需显式传入
        kind, val = unwrap_default(f)
        if kind == "value":
            kw[name] = val
        elif kind == "factory":
            try:
                kw[name] = val()
            except Exception:
                missing.append(name)
        else:
            missing.append(name)

    for k, v in base_kwargs(cls_name, fields).items():
        kw[k] = v
        if k in missing:
            missing.remove(k)

    for name in list(missing):
        if name in GENERIC_FALLBACK:
            kw[name] = GENERIC_FALLBACK[name]
            missing.remove(name)
    if missing:
        return None, f"缺必填字段且无基线值: {missing}"

    direct = {}
    nested = {}   # field_name -> {"cls","file","overrides"}
    problems = []
    for k, v in (assign or {}).items():
        key = k.replace("self.", "")
        if "." in key:
            head, tail = key.split(".", 1)
            inner = tail.split(".")[-1]
            if head not in fields:
                problems.append(f"未知嵌套前缀 {head}")
                continue
            holder = None
            for entry in IDX.get(inner, []):
                if entry["class"] not in (cls_name, "EngineArgs"):
                    holder = entry
                    break
            if holder is None:
                problems.append(f"找不到 {inner} 的持有类")
                continue
            spec = nested.setdefault(head, {"cls": holder["class"], "file": holder.get("file"), "overrides": {}})
            spec["overrides"][inner] = v
        elif key in fields or key in EXTRA_ASSIGN_KEYS.get(cls_name, set()):
            if isinstance(v, dict) and v and key in fields:
                guess = guess_holder_from_dict(v)
                if guess:
                    obj, err = build_nested_multi(guess[0], guess[1], v)
                    if obj is not None:
                        direct[key] = obj
                        continue
                direct[key] = v  # 猜测失败：直传（留待人工复核）
            else:
                direct[key] = v
        else:
            # 未知键 → 尝试嵌套注入（VllmConfig.xxx_config 机制）
            nmap = NESTED_FIELD_MAP.get(cls_name, {})
            holder = None
            field_name = None
            for entry in IDX.get(key, []):
                fn = nmap.get(entry["class"])
                if fn and fn in fields:
                    holder = entry
                    field_name = fn
                    break
            if holder is None:
                problems.append(f"字段 {key} 不属于 {cls_name}（且无法嵌套注入）")
            else:
                spec = nested.setdefault(field_name, {"cls": holder["class"], "file": holder.get("file"), "overrides": {}})
                spec["overrides"][key] = v

    if problems:
        return None, "; ".join(problems)
    kw.update(direct)
    for field_name, spec in nested.items():
        obj, err = build_nested_multi(spec["cls"], spec["file"], spec["overrides"])
        if obj is None:
            return None, f"嵌套注入 {field_name} 失败: {err}"
        kw[field_name] = obj
    return kw, None


def attempt(cls, cls_name, assign=None):
    kw, problem = build_kwargs(cls, cls_name, assign or {})
    if kw is None:
        return None, problem
    try:
        cls(**kw)
        return True, "constructed_ok"
    except Exception as ex:
        msg = str(ex).replace("\n", " ")[:400]
        return False, f"{type(ex).__name__}: {msg}"


def main():
    global IDX
    args = sys.argv[1:]
    cases_path, rec_path = CASES_DEFAULT, REC_DEFAULT
    limit, only = None, None
    rest = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--limit":
            limit = int(args[i + 1]); i += 2
        elif a == "--only":
            only = args[i + 1]; i += 2
        else:
            rest.append(a); i += 1
    if rest:
        cases_path = rest[0]
    if len(rest) > 1:
        rec_path = rest[1]

    print(f"cases={cases_path}")
    cases_doc = load_json(cases_path)
    IDX = param_index()

    import vllm
    print("vllm version:", vllm.__version__)

    records, counts = [], {}
    for case in cases_doc.get("cases", []):
        cid = case.get("constraint_id")
        if only and cid != only:
            continue
        if limit is not None and len(records) >= limit:
            break
        assign = case.get("violation_assignment") or {}
        params = case.get("params") or []
        expr = case.get("expr")
        rec = {
            "constraint_id": cid, "track": "A", "engine": "vllm-0.30.0",
            "expr": expr, "config": assign, "violates": expr,
            "run_at": datetime.now(timezone.utc).isoformat(),
        }

        # 候选类 = 参数所属类 ∪ 赋值键所属类（键权重更高），VllmConfig 兜底
        keys_for_rank = list(params) + [k.replace("self.", "").split(".")[-1] for k in assign.keys()]
        class_hits = {}
        for p in keys_for_rank:
            for entry in IDX.get(p, []):
                hit = class_hits.setdefault(entry["class"], {"keys": set(), "file": entry.get("file")})
                hit["keys"].add(p)
        candidates = sorted(class_hits.items(), key=lambda kv: -len(kv[1]["keys"]))
        if "VllmConfig" not in class_hits:
            candidates.append(("VllmConfig", {"keys": set(), "file": "vllm/config/vllm.py"}))

        result = None
        for cls_name, hit in candidates:
            if cls_name in ("EngineArgs",):
                continue
            cls = import_class(cls_name, hit.get("file"))
            if cls is None:
                continue
            b_ok, b_detail = attempt(cls, cls_name, None)
            if b_ok is None:
                continue
            if not b_ok:
                result = (f"S1:{cls_name}", False, f"baseline_fail: {b_detail}", False)
                continue
            v_ok, v_detail = attempt(cls, cls_name, assign)
            if v_ok is None:
                result = (f"S1:{cls_name}", False, f"assign_fail: {v_detail}", False)
                continue
            result = (f"S1:{cls_name}", True, v_detail, not v_ok)
            break

        if result is None:
            rec.update({"status": "blocked", "detail": "无可构造的候选类"})
        else:
            how, baseline_ok, detail, verified = result
            rec["strategy"] = how
            if not baseline_ok:
                rec.update({"status": "blocked", "detail": detail})
            elif verified:
                rec.update({"status": "confirmed", "observed": detail})
            else:
                rec.update({"status": "no_error", "observed": detail,
                            "note": "基线可构造，但违反赋值未在构造期报错"})
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
        records.append(rec)
        print(f'{cid}: {rec["status"]:9s} {rec.get("strategy","-"):22s} '
              f'{str(rec.get("observed") or rec.get("detail"))[:105]}')

    with open(rec_path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nsummary={counts} -> {rec_path}")


if __name__ == "__main__":
    main()
