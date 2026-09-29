# -*- coding: utf-8 -*-
"""回填 3 处审查发现（缺前置条件）到扩展图 audit_note，并生成审查记录"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REC = r"F:\文献\AgentOps\实验记录"
GRAPH = os.path.join(REC, "约束图-v1-ext.json")

NOTE_MAP = {
    "1": "独立对抗审查（2026-09-28）：该 raise 仅覆盖 model=None 且 num_speculative_tokens 非空的分支；method=mtp 且 model 未设时 post_init 通过（前置条件已注明）。",
    "15": "独立对抗审查（2026-09-28）：该校验仅在 ngram/ngram_gpu 分支生效；method='suffix' 时不经过此检查（前置条件已注明）。",
    "26": "独立对抗审查（2026-09-28）：该校验仅在 method='suffix' 分支生效；method='ngram_gpu' 时不经过此检查（前置条件已注明）。",
}


def main():
    sample = json.load(open(os.path.join(REC, "独立审查-约束样本.json"), encoding="utf-8"))["sampled"]
    verdicts = json.load(open(os.path.join(REC, "独立审查-约束结果.json"), encoding="utf-8"))["verdicts"]
    targets = {}
    for pos, note in NOTE_MAP.items():
        cid = sample[int(pos) - 1]["id"]
        targets[cid] = note
        print(f"pos {pos} -> {cid}: {verdicts[pos]['reason']}")

    g = json.load(open(GRAPH, encoding="utf-8"))
    hit = 0
    for n in g["nodes"]:
        if n.get("id") in targets:
            n["audit_note"] = targets[n["id"]]
            hit += 1
    json.dump(g, open(GRAPH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"audit_note added: {hit}/{len(targets)}")


if __name__ == "__main__":
    main()
