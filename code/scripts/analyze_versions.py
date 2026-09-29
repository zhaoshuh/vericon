# -*- coding: utf-8 -*-
"""P2 · 纵向版本分析（静态层）：
1. 各版本参数面：CLI flags / Config 字段 / 候选校验点 的数量与集合
2. 跨版本 churn：新增/删除的 flags 与 config 字段
3. 三条 SCOOT 规则的源码级存在性检查（grep 关键行）

输出: 实验记录/P2-版本研究/版本对比.json / 版本对比.md
"""
import json
import os
import re
import sys

REC = r"F:\文献\AgentOps\实验记录\P2-版本研究"
TP = r"F:\文献\AgentOps\代码\third_party"
VERSIONS = [
    ("v0.4.2", os.path.join(TP, "vllm-versions", "v0.4.2")),
    ("v0.5.5", os.path.join(TP, "vllm-versions", "v0.5.5")),
    ("v0.6.6", os.path.join(TP, "vllm-versions", "v0.6.6")),
    ("v0.8.0", os.path.join(TP, "vllm-versions", "v0.8.0")),
    ("v0.10.0", os.path.join(TP, "vllm-versions", "v0.10.0")),
    ("v0.30.0", os.path.join(TP, "vllm-v0.30.0")),
]

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_stats(label, root):
    p = json.load(open(os.path.join(REC, f"{label}-params.json"), encoding="utf-8"))
    c = json.load(open(os.path.join(REC, f"{label}-candidates.json"), encoding="utf-8"))
    flags = {f["flag"] for f in p.get("cli_flags", [])}
    cfg_fields = set()
    for x in p["params"]:
        if x["origin"] == "config" or x["class"].endswith("Config"):
            cfg_fields.add(x["name"])
    return {
        "label": label,
        "root": root,
        "params_total": p["counts"]["params_total"],
        "cli_flags": sorted(flags),
        "config_fields": sorted(cfg_fields),
        "candidates": c["counts"]["total"],
        "asserts": c["counts"]["by_kind"].get("assert", 0),
        "if_raise": c["counts"]["by_kind"].get("if-raise", 0),
        "files_scanned": p["meta"]["files_scanned"],
    }


def grep_rule(root, pattern):
    hits = []
    rx = re.compile(pattern)
    for dirpath, dirnames, filenames in os.walk(os.path.join(root, "vllm")):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "tests", "benchmarks", "examples")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                for i, line in enumerate(open(path, encoding="utf-8", errors="ignore"), 1):
                    if rx.search(line):
                        hits.append(f'{os.path.relpath(path, root).replace(chr(92), "/")}:{i}')
            except Exception:
                pass
    return hits


def main():
    stats = [load_stats(l, r) for l, r in VERSIONS]

    # SCOOT 规则源码级检查
    rule_patterns = {
        "R1 mtib>=mns 校验": r"max_num_batched_tokens.*max_num_seqs|max_num_seqs.*max_num_batched_tokens",
        "R2 chunked⊥prefix 同现": r"enable_chunked_prefill.*enable_prefix_caching|enable_prefix_caching.*enable_chunked_prefill",
        "R3 mtib>=max_model_len": r"max_num_batched_tokens.*max_model_len|max_model_len.*max_num_batched_tokens",
    }
    rule_hits = {}
    for s in stats:
        rule_hits[s["label"]] = {k: grep_rule(s["root"], p)[:8] for k, p in rule_patterns.items()}

    # churn
    churn = []
    for i in range(1, len(stats)):
        a, b = stats[i - 1], stats[i]
        fa, fb = set(a["cli_flags"]), set(b["cli_flags"])
        ca, cb = set(a["config_fields"]), set(b["config_fields"])
        churn.append({
            "from": a["label"], "to": b["label"],
            "flags_added": sorted(fb - fa), "flags_removed": sorted(fa - fb),
            "config_added": sorted(cb - ca), "config_removed": sorted(ca - cb),
            "candidates": [a["candidates"], b["candidates"]],
        })

    out = {"versions": stats, "churn": churn, "scoot_rules_source_hits": rule_hits}
    json.dump(out, open(os.path.join(REC, "版本对比.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    md = [
        "# P2 · vLLM 纵向版本对比（静态层）",
        "",
        "| 版本 | 文件数 | 参数总数 | CLI flags | Config 字段 | 校验候选 | assert | if-raise |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in stats:
        md.append(f"| {s['label']} | {s['files_scanned']} | {s['params_total']} | {len(s['cli_flags'])} | "
                  f"{len(s['config_fields'])} | {s['candidates']} | {s['asserts']} | {s['if_raise']} |")
    md += ["", "## 跨版本 churn（相邻版本）", "",
           "| 区间 | flags + | flags − | config + | config − | 候选数变化 |", "|---|---|---|---|---|---|"]
    for ch in churn:
        md.append(f"| {ch['from']} → {ch['to']} | {len(ch['flags_added'])} | {len(ch['flags_removed'])} | "
                  f"{len(ch['config_added'])} | {len(ch['config_removed'])} | {ch['candidates'][0]} → {ch['candidates'][1]} |")
    md += ["", "## SCOOT 三条规则的源码级存在性（每版本前 8 处命中）", ""]
    for label, hits in rule_hits.items():
        md.append(f"### {label}")
        for k, v in hits.items():
            md.append(f"- **{k}**：{'；'.join(v[:3]) if v else '无命中'}{' …' if len(v) > 3 else ''}")
        md.append("")
    md += ["", f"*生成：2026-09-27 ｜ 数据：{REC}*"]
    open(os.path.join(REC, "版本对比.md"), "w", encoding="utf-8").write("\n".join(md))
    print("churn:", json.dumps([{ "seg": f"{c['from']}->{c['to']}", "flags+": len(c['flags_added']), "flags-": len(c['flags_removed']),
                                   "cfg+": len(c['config_added']), "cfg-": len(c['config_removed'])} for c in churn], ensure_ascii=False))
    print("->", os.path.join(REC, "版本对比.md"))


if __name__ == "__main__":
    main()
