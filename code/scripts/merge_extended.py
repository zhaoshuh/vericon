# -*- coding: utf-8 -*-
"""P1a 收口：合并 tier3 批次到 v1 约束图 → 约束图-v1-ext.json（含机械校验与去重）"""
import glob
import importlib.util
import json
import os
from datetime import datetime, timezone

REC = r"F:\文献\AgentOps\实验记录"
SRC_ROOT = r"F:\文献\AgentOps\代码\third_party\vllm-v0.30.0"
BASE = os.path.join(REC, "约束图.json")
PARAMS = os.path.join(REC, "参数清单.json")
TIER3 = os.path.join(REC, "S3_parts_tier3", "batch*.json")
OUT = os.path.join(REC, "约束图-v1-ext.json")


def load_mc():
    spec = importlib.util.spec_from_file_location(
        "mc", r"F:\文献\AgentOps\代码\scripts\merge_constraints.py")
    mc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc)
    return mc


def main():
    mc = load_mc()
    base = json.load(open(BASE, encoding="utf-8"))
    params = json.load(open(PARAMS, encoding="utf-8"))
    param_names = {p["name"] for p in params["params"]} | {c.get("dest") for c in params.get("cli_flags", []) if c.get("dest")}

    seen = {(n.get("expr", "").strip(), tuple(sorted(n.get("params") or []))) for n in base["nodes"]}
    new_nodes, rejected = [], []
    for path in sorted(glob.glob(TIER3)):
        try:
            part = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            rejected.append({"source": os.path.basename(path), "reason": f"parse: {e}"})
            continue
        for c in part.get("constraints", []):
            problems = mc.check(c, param_names, SRC_ROOT)
            if problems:
                rejected.append({"source": os.path.basename(path), "constraint": c, "problems": problems})
                continue
            key = (c.get("expr", "").strip(), tuple(sorted(c.get("params") or [])))
            if key in seen:
                continue
            seen.add(key)
            new_nodes.append(c)

    start = len(base["nodes"]) + 1
    for i, c in enumerate(new_nodes):
        c["id"] = f"C{start + i:03d}"
        c.setdefault("validation", {"status": "not_tested", "method": None, "run_id": None,
                                    "note": "tier3 全量召回新增；待 S4 证伪"})
    out = dict(base)
    out["nodes"] = base["nodes"] + new_nodes
    out["meta"]["extended_at"] = datetime.now(timezone.utc).isoformat()
    out["meta"]["extension"] = "P1a 全量召回：tier3 批次（10 批，2,766 候选）"
    out["stats"]["total_ext"] = len(out["nodes"])
    out["stats"]["new_from_tier3"] = len(new_nodes)
    out["stats"]["rejected_tier3"] = len(rejected)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"base": len(base["nodes"]), "new": len(new_nodes),
                      "total": len(out["nodes"]), "rejected": len(rejected)}, ensure_ascii=False))
    print("->", OUT)


if __name__ == "__main__":
    main()
