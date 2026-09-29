# -*- coding: utf-8 -*-
"""P3 收口：vLLM vs SGLang 跨引擎约束对比（类型/规模/家族）

用法: python compare_engines.py [vllm_graph] [sglang_graph]
输出: 实验记录/跨引擎对比.md + .json
"""
import json
import os
import sys
from collections import Counter

REC = r"F:\文献\AgentOps\实验记录"
VLLM = os.path.join(REC, "约束图-v1-ext.json")
SGL = os.path.join(REC, "约束图-sglang.json")
OUT_MD = os.path.join(REC, "跨引擎对比.md")
OUT_JSON = os.path.join(REC, "跨引擎对比.json")

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FAMILY_HINTS = [
    ("batch/token 预算", ["batch", "token"]),
    ("并行/拓扑", ["parallel", "tp", "pp", "dp", "world", "rank"]),
    ("KV cache/内存", ["kv", "cache", "memory", "block", "mem"]),
    ("量化/精度", ["quant", "fp8", "int8", "dtype"]),
    ("投机解码", ["spec", "draft", "eagle", "mtp"]),
    ("调度/策略", ["schedul", "policy", "chunk"]),
    ("多模态", ["mm_", "multimodal", "image", "audio", "video"]),
    ("LoRA/适配器", ["lora", "adapter"]),
    ("分布式通信", ["communicat", "nccl", "allreduce", "all2all", "connector"]),
]


def stats(graph):
    nodes = graph["nodes"]
    return {
        "total": len(nodes),
        "types": dict(Counter(n.get("type") for n in nodes).most_common()),
        "scopes_top": dict(Counter(n.get("scope") for n in nodes).most_common(12)),
        "evidence_100": all(n.get("evidence") for n in nodes),
    }


def families(nodes):
    cnt = Counter()
    for n in nodes:
        text = (n.get("expr", "") + " " + json.dumps(n.get("params", []))).lower()
        for fam, kws in FAMILY_HINTS:
            if any(k in text for k in kws):
                cnt[fam] += 1
    return dict(cnt.most_common())


def main():
    vp = sys.argv[1] if len(sys.argv) > 1 else VLLM
    sp = sys.argv[2] if len(sys.argv) > 2 else SGL
    v = json.load(open(vp, encoding="utf-8"))
    s = json.load(open(sp, encoding="utf-8"))
    vs, ss = stats(v), stats(s)
    vf, sf = families(v["nodes"]), families(s["nodes"])

    out = {"vllm": {**vs, "families": vf, "graph": vp}, "sglang": {**ss, "families": sf, "graph": sp}}
    json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    md = [
        "# P3 · 跨引擎约束对比（vLLM vs SGLang）",
        "",
        "| 指标 | vLLM v0.30.0（ext） | SGLang v0.5.20 |",
        "|---|---|---|",
        f"| 约束总数 | {vs['total']} | {ss['total']} |",
        f"| 100% 带证据 | {'✅' if vs['evidence_100'] else '❌'} | {'✅' if ss['evidence_100'] else '❌'} |",
        "",
        "## 类型分布",
        "",
        "| 类型 | vLLM | SGLang |",
        "|---|---|---|",
    ]
    for t in sorted(set(list(vs["types"]) + list(ss["types"]))):
        md.append(f"| {t} | {vs['types'].get(t, 0)} | {ss['types'].get(t, 0)} |")
    md += ["", "## 约束家族（按表达式/参数关键词粗分类）", "",
           "| 家族 | vLLM | SGLang |", "|---|---|---|"]
    for fam, _ in FAMILY_HINTS:
        md.append(f"| {fam} | {vf.get(fam, 0)} | {sf.get(fam, 0)} |")
    md += ["", "## 主要 scope", "",
           f"- vLLM：{', '.join(f'{k}({v})' for k, v in list(vs['scopes_top'].items())[:10])}",
           f"- SGLang：{', '.join(f'{k}({v})' for k, v in list(ss['scopes_top'].items())[:10])}",
           "", f"*生成：2026-09-27 ｜ 数据：{vp} / {sp}*"]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))
    print(json.dumps({"vllm_total": vs["total"], "sglang_total": ss["total"],
                      "vllm_families": vf, "sglang_families": sf}, ensure_ascii=False, indent=1))
    print("->", OUT_MD)


if __name__ == "__main__":
    main()
