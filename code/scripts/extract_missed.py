# -*- coding: utf-8 -*-
"""P1b 定向补抽：提取 tier3 漏抽的真约束站点 → S3_parts_tier3/_inputs/missed.json"""
import json
import os

REC = r"F:\文献\AgentOps\实验记录"
LABELS = os.path.join(REC, "P1b-标注结果.json")
SAMPLE = os.path.join(REC, "P1b-金标准样本.json")
OUT = os.path.join(REC, "S3_parts_tier3", "_inputs", "missed.json")


def main():
    lab = json.load(open(LABELS, encoding="utf-8"))
    sample = json.load(open(SAMPLE, encoding="utf-8"))["sites"]
    missed = []
    for r in lab["rows"]:
        if r["label"] == "C" and r["tier"] == 3 and not r["captured_pm1"]:
            s = sample[r["idx"] - 1]
            missed.append(s)
    payload = {
        "task": "tier3-missed",
        "meta": {"note": "金标准评测识别出的 tier3 漏抽站点（已人工核实为真约束）；定向补抽"},
        "counts": {"candidates": len(missed)},
        "candidates": missed,
    }
    json.dump(payload, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"missed={len(missed)} -> {OUT}")
    for s in missed:
        print(" ", s["file"] + ":" + str(s["line"]), "|", (s.get("condition") or "")[:90])


if __name__ == "__main__":
    main()
