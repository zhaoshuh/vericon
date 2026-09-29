# -*- coding: utf-8 -*-
"""P3 · SGLang 候选预处理：
- 只保留 python/sglang/srt/（推理服务核心），排除 test/multimodal_gen/kernels 等
- 白名单 = ServerArgs / *Args / *Config 类字段 + CLI flags
- 按参数名命中过滤 → 切 4 批 → 输出 S3_sglang/_inputs/batchNN.json
"""
import json
import os
import re
import sys
from collections import Counter

REC = r"F:\文献\AgentOps\实验记录"
PARAMS = os.path.join(REC, "P3-sglang", "sglang-v0.5.20-params.json")
CANDS = os.path.join(REC, "P3-sglang", "sglang-v0.5.20-candidates.json")
OUT = os.path.join(REC, "S3_sglang", "_inputs")

GENERIC = {"type", "name", "mode", "value", "data", "size", "config", "model", "device", "backend"}

# 配置相关核心文件（P3 聚焦：ServerArgs 校验层 + 调度/缓存/管理器）
PRIORITY_PREFIXES = (
    "python/sglang/srt/server_args.py",
    "python/sglang/srt/arg_groups/",
    "python/sglang/srt/scheduler.py",
    "python/sglang/srt/managers/",
    "python/sglang/srt/mem_cache/",
    "python/sglang/srt/configs/",
    "python/sglang/srt/server.py",
    "python/sglang/srt/entrypoints/engine.py",
    "python/sglang/srt/global_config.py",
)


def main():
    p = json.load(open(PARAMS, encoding="utf-8"))
    whitelist = set()
    for x in p["params"]:
        cls = x["class"]
        if cls == "ServerArgs" or cls.endswith("Args") or cls.endswith("Config"):
            whitelist.add(x["name"])
    for c in p.get("cli_flags", []):
        if c.get("dest"):
            whitelist.add(c["dest"])
    whitelist = {n for n in whitelist if len(n) >= 4 and n not in GENERIC}
    print(f"whitelist size: {len(whitelist)}")

    pat = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(re.escape(n) for n in sorted(whitelist, key=len, reverse=True)) + r")(?![A-Za-z0-9_])")

    c = json.load(open(CANDS, encoding="utf-8"))
    kept = []
    for x in c["candidates"]:
        f = x["file"]
        if not f.startswith("python/sglang/srt/"):
            continue
        if "/test" in f or "test_" in os.path.basename(f):
            continue
        if not f.startswith(PRIORITY_PREFIXES):
            continue
        text = " ".join(str(y) for y in [x.get("condition"), x.get("message"), x.get("evidence"), x.get("function"), x.get("class")] if y)
        hit = sorted(set(pat.findall(text)) - GENERIC)
        if not hit:
            continue
        x2 = dict(x)
        x2["matched_params"] = hit
        kept.append(x2)

    print(f"kept: {len(kept)}  files: {len(Counter(x['file'] for x in kept))}")
    print("top files:", Counter(x["file"] for x in kept).most_common(10))

    kept.sort(key=lambda x: (x["file"], x["line"]))
    n_batches = 6
    per = (len(kept) + n_batches - 1) // n_batches
    os.makedirs(OUT, exist_ok=True)
    for i in range(n_batches):
        chunk = kept[i * per:(i + 1) * per]
        if not chunk:
            continue
        payload = {
            "task": f"sglang-batch{i+1:02d}",
            "meta": {"engine": "sglang", "version": "v0.5.20",
                     "note": "只保留配置参数之间/取值的约束；内部实现检查 dropped"},
            "counts": {"candidates": len(chunk), "files": dict(Counter(x["file"] for x in chunk).most_common(30))},
            "candidates": chunk,
        }
        pth = os.path.join(OUT, f"batch{i+1:02d}.json")
        json.dump(payload, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"batch{i+1:02d}: {len(chunk)} -> {pth}")
    print("SGLANG PREP DONE")


if __name__ == "__main__":
    main()
