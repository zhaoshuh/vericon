# -*- coding: utf-8 -*-
"""S3 · 候选预过滤（LLM + 静态分析混合的第一步）

思路：13301 条静态候选里绝大多数是内部实现检查；真正与"配置参数"相关的是少数。
用参数清单里的真实参数名（config 字段 + EngineArgs 字段 + CLI dest）做词边界匹配，
只保留"声称与某个配置参数有关"的候选 → 大幅缩小 agent 精读范围（同时保留全文供回溯）。

输入: 实验记录/参数清单.json, 实验记录/约束候选_静态.json
输出: 实验记录/约束候选-配置相关.json
用法: python filter_candidates.py
"""
import json
import re
import sys
from collections import Counter

DEFAULT_PARAMS = r"F:\文献\AgentOps\实验记录\参数清单.json"
DEFAULT_CANDS = r"F:\文献\AgentOps\实验记录\约束候选_静态.json"
DEFAULT_OUT = r"F:\文献\AgentOps\实验记录\约束候选-配置相关.json"

# 过短/过通用的名字容易误匹配，单独标记而非排除
GENERIC = {"seed", "dtype", "model", "enforce_eager", "disable_log_stats", "max_tokens",
           "device", "revision", "tokenizer", "trust_remote_code", "download_dir", "load_format"}


def main():
    params_json = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PARAMS
    cands_json = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CANDS
    out_json = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUT

    with open(params_json, encoding="utf-8") as f:
        plist = json.load(f)
    names = set()
    for p in plist.get("params", []):
        if p.get("origin") in ("config", "engine_args"):
            names.add(p["name"])
    for c in plist.get("cli_flags", []):
        if c.get("dest"):
            names.add(c["dest"])
    names = {n for n in names if len(n) >= 4}
    pat = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")(?![A-Za-z0-9_])")

    with open(cands_json, encoding="utf-8") as f:
        cands = json.load(f)

    kept = []
    tier_counter = Counter()
    kind_counter = Counter()
    file_counter = Counter()
    for c in cands.get("candidates", []):
        text = " ".join(str(x) for x in [c.get("condition"), c.get("message"), c.get("evidence"),
                                         c.get("function"), c.get("class")] if x)
        hit = sorted(set(pat.findall(text)) - GENERIC)
        if not hit:
            continue
        c2 = dict(c)
        c2["matched_params"] = hit
        c2["generic_hit"] = sorted(set(pat.findall(text)) & GENERIC)
        kept.append(c2)
        tier_counter[c["tier"]] += 1
        kind_counter[c["kind"]] += 1
        file_counter[c["file"]] += 1

    result = {
        "meta": {
            "source_candidates": cands.get("meta", {}),
            "param_names_used": len(names),
            "note": "已按参数名命中过滤；沿用候选的 tier 分层（1=config/，2=engine/core/，3=其余）",
        },
        "counts": {
            "kept": len(kept),
            "by_tier": dict(sorted(tier_counter.items())),
            "by_kind": dict(kind_counter),
            "top_files": file_counter.most_common(25),
        },
        "candidates": kept,
    }
    import os
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result["counts"], ensure_ascii=False, indent=2))

    # 打印少量样本便于人工检查过滤质量
    print("\n--- 样本（tier 1/2，前 20 条）---")
    shown = 0
    for c in kept:
        if c["tier"] <= 2:
            print(f'[{c["tier"]}] {c["file"]}:{c["line"]} ({c["kind"]}) matched={c["matched_params"]}')
            print(f'    cond: {(c.get("condition") or "")[:160]}')
            shown += 1
            if shown >= 20:
                break


if __name__ == "__main__":
    main()
