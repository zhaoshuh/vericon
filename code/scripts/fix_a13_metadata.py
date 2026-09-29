# -*- coding: utf-8 -*-
"""A13 产物元数据修正（2026-09-29）
①. SGLang 图/参数文件 meta.commit 误填 vLLM 提交号 → 更正为 v0.5.20 tag 对应 commit（GitHub API 核验）
②. 约束图-v1-ext.json stats：total/with_evidence/by_type/by_scope 由「仅基础层 282」更正为「全量 716」
③. P2-版本研究/版本对比.md：CLI flags 列 259（去重）与 参数清单 262（注册）口径注明
④. S6-真机锚点-报告.md 首页：165.4（旧 2-rep 轮）→ 159.77（主口径 5-rep）
"""
import json
import os
import shutil
from collections import Counter

def backup(p):
    b = p + ".pre-a13-20260929.bak"
    if not os.path.exists(b):
        shutil.copy2(p, b)

SG_COMMIT = "94602c9c2b7cbdb8efd5c52802dac6a1c180089e"
SG_NOTE = ("tag v0.5.20 → commit（GitHub API 核验 2026-09-29，annotated tag d158602\u2026\uff09；"
           "原值 ced6857\u2026 系 vLLM v0.30.0 提交号误填）")

# ---------- ① SGLang 三处 ----------
sg_files = [
    "/mnt/f/文献/AgentOps/实验记录/约束图-sglang.json",
    "/mnt/f/文献/AgentOps/实验记录/P3-sglang/sglang-v0.5.20-params.json",
    "/mnt/f/文献/AgentOps/论文Q4/复现包/graph/constraint-graph-sglang.json",
]
for p in sg_files:
    backup(p)
    d = json.load(open(p, encoding="utf-8"))
    old = d["meta"].get("commit")
    d["meta"]["commit"] = SG_COMMIT
    d["meta"]["commit_note"] = SG_NOTE
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[1] {p}\n    {old} -> {SG_COMMIT}")

# ---------- ② ext 图 stats ----------
p = "/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json"
backup(p)
d = json.load(open(p, encoding="utf-8"))
nodes = d["nodes"]
st = d["stats"]
print("[2] meta 原样:", json.dumps(d.get("meta", {}), ensure_ascii=False)[:300])
st["total"] = len(nodes)
st["with_evidence"] = sum(1 for x in nodes if str(x.get("evidence", "")).strip())
st["by_type"] = dict(Counter(x.get("type") for x in nodes))
st["by_scope"] = dict(Counter(x.get("scope") for x in nodes))
st["tiers"] = {"config_engine_tiers": 282, "tier3_extension": 434}
st["stats_note"] = ("2026-09-29 更正（审稿 A13）：total/with_evidence/by_type/by_scope 原仅统计基础层 282 节点，"
                    "已更新为全量 716；tiers 拆分为合并时记录（282+434=716）。")
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"[2] total={st['total']} with_evidence={st['with_evidence']} by_type={st['by_type']}")

# ---------- ③ 版本对比.md ----------
p = "/mnt/f/文献/AgentOps/实验记录/P2-版本研究/版本对比.md"
backup(p)
t = open(p, encoding="utf-8").read()
h_old = "| 版本 | 文件数 | 参数总数 | CLI flags | Config 字段 | 校验候选 | assert | if-raise |"
h_new = "| 版本 | 文件数 | 参数总数 | CLI flags（去重） | Config 字段 | 校验候选 | assert | if-raise |"
assert t.count(h_old) == 1
t = t.replace(h_old, h_new, 1)
row = "| v0.30.0 | 2454 | 9670 | 259 | 1002 | 13301 | 8498 | 4803 |"
assert t.count(row) == 1
note = ("\n\n> 注：**CLI flags 列为去重后的 flag 名**；v0.30.0 = **259 去重 / 262 处 `add_argument` 注册**"
        "（后者见 `参数清单.json` 的 `counts.cli_flags=262`，论文口径\u201c262 注册、259 去重\u201d，A13 已核）。")
t = t.replace(row, row + note, 1)
open(p, "w", encoding="utf-8", newline="").write(t)
print("[3] 版本对比.md 已注明两口径")

# ---------- ④ S6 报告 ----------
p = "/mnt/f/文献/AgentOps/实验记录/S6-真机锚点-报告.md"
backup(p)
t = open(p, encoding="utf-8").read()
old = "| Phase B（真实性能） | 24 配置实测：**pp512 最高 165.4 tok/s（t=4,b=512,ub=256）**；tg64 最高 44.3 tok/s；每配置 wall 17–24s |"
new = ("| Phase B（真实性能） | 24 配置实测（主口径 5-rep `llamacpp_anchor_5rep.csv`）：**pp512 最高 159.77 tok/s"
       "（t=4,b=256,ub=128）**；tg64 最高 45.86 tok/s（t=4,b=512,ub=128）；每配置 wall 30–73s |")
assert t.count(old) == 1
t = t.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(t)
print("[4] S6 报告首页已更正为 5-rep 主口径")
print("A13 ALL DONE")
