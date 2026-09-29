# -*- coding: utf-8 -*-
"""导师复核后的小修正：给约束图加 audit 注记 + C004 补一条证据（不改类型/ID，保持版本稳定）"""
import json
from datetime import datetime, timezone

GRAPH = r"F:\文献\AgentOps\实验记录\约束图.json"

g = json.load(open(GRAPH, encoding="utf-8"))
by_id = {n["id"]: n for n in g["nodes"]}
now = datetime.now(timezone.utc).isoformat()

# C004：补上 int 分支证据（导师复核发现 1138 行）
c = by_id.get("C004")
if c is not None:
    ev = c.setdefault("evidence", [])
    if not any(e.get("line") == 1138 and e.get("file", "").endswith("compilation.py") for e in ev):
        ev.append({"file": "vllm/config/compilation.py", "line": 1138,
                   "snippet": "assert isinstance(x, int)"})
    c.setdefault("audit", {})["advisor_2026-09-27"] = "复核通过；补 int 分支证据（行 1138）"

notes = {
    "C058": "第一批抽检 ⚠️：scheduler_block_size 公式为解释性改写（实际 math.lcm(group_block_sizes)）；运行期路径",
    "C053": "第一批抽检 ⚠️：运行期/环境相关路径；表述为方向性约束",
    "C017": "第一批抽检 ⚠️：报错信息的解释性归纳；方向正确",
    "C016": "第一批抽检 ⚠️：措辞应精确为“不含任何 attention op”；关系成立",
    "C062": "导师复核注：代码对任意 ≠0 的 retention_interval 均报错；本约束表述保守（>0），不影响正确性",
    "C254": "导师复核注：类型标签 mutual_exclusion 可接受（{flag=True} 与 {PP>1} 互斥）；等价于 implication",
}
for cid, note in notes.items():
    n = by_id.get(cid)
    if n is not None:
        n.setdefault("audit", {})["advisor_2026-09-27"] = note

g.setdefault("meta", {})["advisor_review"] = {
    "date": "2026-09-27",
    "scope": "两批独立抽样共 40 条（seed 42 / seed 20260927），0 错误；G1 复核通过",
    "record": "实验记录/G1-约束抽检-第一批.md（含导师复核节）",
}

json.dump(g, open(GRAPH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("audit notes applied:", list(notes.keys()) + ["C004"])
