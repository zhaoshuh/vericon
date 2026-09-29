# -*- coding: utf-8 -*-
"""S4 · 合并 4 份用例文件 → cases.json（去重、统计）

输入:  实验记录/S4验证/cases_part{1..4}.json
输出:  实验记录/S4验证/cases.json
用法:  python merge_s4_cases.py
"""
import glob
import json
import os
from datetime import datetime, timezone

PARTS = r"F:\文献\AgentOps\实验记录\S4验证\cases_part*.json"
OUT = r"F:\文献\AgentOps\实验记录\S4验证\cases.json"


def main():
    cases, skipped, seen = [], [], set()
    for path in sorted(glob.glob(PARTS)):
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        for c in doc.get("cases", []):
            cid = c.get("constraint_id")
            if cid in seen:
                continue
            seen.add(cid)
            c.setdefault("source_part", os.path.basename(path))
            cases.append(c)
        for s in doc.get("skipped", []):
            s["source_part"] = os.path.basename(path)
            skipped.append(s)

    cases.sort(key=lambda c: str(c.get("constraint_id")))
    out = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "note": "S4 用例（构造期违反赋值）。skipped 为不可在构造期构造的约束（运行期/请求期/环境依赖）。",
        },
        "counts": {"cases": len(cases), "skipped": len(skipped)},
        "cases": cases,
        "skipped": skipped,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out["counts"], ensure_ascii=False), "->", OUT)


if __name__ == "__main__":
    main()
