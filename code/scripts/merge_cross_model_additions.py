# -*- coding: utf-8 -*-
"""把跨模型新增的 2 条 confirmed 并入 artifact：
- 回填 约束图-model2.json 的 validation
- 追加到 已验证约束.json（cross_model_additions），更新 stats
"""
import json
from datetime import datetime, timezone

ROOT = r"F:\文献\AgentOps\实验记录"
G2 = ROOT + r"\约束图-model2.json"
REC2 = ROOT + r"\S4验证\records_model2.jsonl"
OK = ROOT + r"\已验证约束.json"

# 读 records（同 id 取最后一条）
recs = {}
for line in open(REC2, encoding="utf-8"):
    line = line.strip()
    if line:
        r = json.loads(line)
        recs[r["constraint_id"]] = r

g2 = json.load(open(G2, encoding="utf-8"))
by_id = {n["id"]: n for n in g2["nodes"]}

added = []
for cid in ("C113", "C193"):
    r = recs.get(cid)
    n = by_id.get(cid)
    if not r or not n:
        print("missing", cid)
        continue
    n["validation"] = {
        "status": r["status"], "track": "A", "engine": r.get("engine"),
        "strategy": r.get("strategy"),
        "observed": (r.get("observed") or "")[:500],
        "run_at": r.get("run_at"),
        "source": "S4-trackA（跨模型新增，2026-09-27）",
    }
    if r["status"] == "confirmed":
        added.append(n)

json.dump(g2, open(G2, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

ok = json.load(open(OK, encoding="utf-8"))
PRIMARY = 111  # 主批次 confirmed（固定值，保证脚本幂等）
ok["stats"]["confirmed_primary"] = PRIMARY
ok["stats"]["cross_model_additions"] = len(added)
ok["stats"]["confirmed"] = PRIMARY + len(added)
ok["meta"]["cross_model_note"] = (
    "2026-09-27 跨模型复现（GLM-5.3-Flash）新增 34 条候选，其中 2 条（C113/C193）经 S4 执行证伪确认并入；"
    "其余 32 条经用例构造判定为运行期/请求期/环境依赖（理由见 S4验证/cases_model2.json）。"
)
ok["meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
ok["stats"]["confirmed_ratio_all"] = round(
    ok["stats"]["confirmed"] / max(1, ok["stats"].get("graph_total", 282)), 3
)
existing_ids = {c["id"] for c in ok["constraints"]}
for n in added:
    n2 = dict(n)
    n2["id"] = "CM-" + n["id"]          # 跨模型新增：加前缀避免与主批次编号冲突
    n2["cross_model_source"] = "GLM-5.3-Flash 批次"
    if n2["id"] not in existing_ids:
        ok["constraints"].append(n2)
        existing_ids.add(n2["id"])
json.dump(ok, open(OK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(json.dumps(ok["stats"], ensure_ascii=False))
print("added:", [("CM-" + n["id"]) for n in added])
print("constraints total:", len(ok["constraints"]))
