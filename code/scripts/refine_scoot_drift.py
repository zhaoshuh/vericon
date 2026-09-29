# -*- coding: utf-8 -*-
"""给 scoot-drift.json 补深查修正注记（R2/R3 口径修正）"""
import json

P = r"F:\文献\AgentOps\实验记录\S4验证\scoot-drift.json"
d = json.load(open(P, encoding="utf-8"))
d["refinement_2026_09_27"] = {
    "source": "实验记录/P2-版本研究/SCOOT规则深查.md（v0.4.2/v0.5.5 源码级复核）",
    "R1": "跨 5 个版本（0.4.2→0.30.0）稳定存在（v0.5.5: config.py:938-942 逐字同款）",
    "R2": "修正：0.4.2/0.5.5 源码中均无互斥校验（±6 行窗口零同现）；v0.5.5 唯一交互是'未开 prefix caching 时自动开 chunked prefill'（arg_utils.py:833-838）→ 该规则很可能从未是代码约束，属人工过度断言",
    "R3": "修正：条件式语义在 v0.5.5 就存在（config.py:927-936），非'语义变化'；变化在默认值（V1 默认开 chunked prefill）→ 实际约束力显著下降",
    "verdict_refined": {
        "SCOOT#1": "跨 5 版本稳定",
        "SCOOT#2": "很可能从未在源码中成立（人工过度断言）",
        "SCOOT#3": "语义一致；因默认值变化而失去实际约束力",
    },
}
json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("updated:", P)
