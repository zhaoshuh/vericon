# -*- coding: utf-8 -*-
"""标签敏感性：在第二批 60 站点盲标子集上，用更严格标签口径重算召回"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REC = r"F:\文献\AgentOps\实验记录"

POS = list(range(1, 21)) + list(range(51, 71)) + list(range(101, 121))


def main():
    rows = {r["idx"]: r for r in json.load(open(os.path.join(REC, "P1b-标注结果2.json"), encoding="utf-8"))["rows"]}
    second = json.load(open(os.path.join(REC, "P1b-第二标注-结果2.json"), encoding="utf-8"))["labels"]

    strict_C = [p for p in POS if second.get(str(p), {}).get("label") == "C"]
    mine_C = [p for p in POS if rows[p]["label"] == "C"]

    def recall(idxs):
        cap_e = sum(1 for p in idxs if rows[p]["captured_exact"])
        cap_p = sum(1 for p in idxs if rows[p]["captured_pm1"])
        return {"n": len(idxs), "exact": round(cap_e / len(idxs), 4), "pm1": round(cap_p / len(idxs), 4)}

    out = {
        "subset": 60,
        "evaluator_labels": {"C": len(mine_C), **recall(mine_C)},
        "strict_labeler_labels": {"C": len(strict_C), **recall(strict_C)},
        "excluded_by_strict": [p for p in mine_C if p not in strict_C],
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
