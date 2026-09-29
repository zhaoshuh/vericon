# -*- coding: utf-8 -*-
"""独立审查汇总：① 约束审查统计 ② 站点盲标一致性（vs 我方标签）"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REC = r"F:\文献\AgentOps\实验记录"


def main():
    # ---- ① 约束审查 ----
    cv = json.load(open(os.path.join(REC, "独立审查-约束结果.json"), encoding="utf-8"))["verdicts"]
    from collections import Counter
    cnt = Counter(v["verdict"] for v in cv.values())
    print("== 约束审查 ==", dict(cnt))
    for k, v in cv.items():
        if v["verdict"] != "correct":
            print(f"  [{k}] {v['verdict']}: {v['reason']} | counterexample: {v.get('counterexample','')[:100]}")

    # ---- ② 站点盲标一致性 ----
    sample = json.load(open(os.path.join(REC, "独立审查-站点样本.json"), encoding="utf-8"))["items"]
    second = json.load(open(os.path.join(REC, "独立审查-站点结果.json"), encoding="utf-8"))["labels"]
    lab1 = {r["idx"]: r["label"] for r in json.load(open(os.path.join(REC, "P1b-标注结果.json"), encoding="utf-8"))["rows"]}
    lab2 = {r["idx"]: r["label"] for r in json.load(open(os.path.join(REC, "P1b-标注结果2.json"), encoding="utf-8"))["rows"]}

    pairs = []
    for i, it in enumerate(sample, 1):
        mine = lab1.get(it["idx"]) if it["batch"] == 1 else lab2.get(it["idx"])
        theirs = second.get(str(i), {}).get("label")
        if mine in ("C", "N") and theirs in ("C", "N"):
            pairs.append((i, it["batch"], it["idx"], it["tier"], mine, theirs))

    n = len(pairs)
    a_c = sum(1 for *_, x, y in pairs if x == "C" and y == "C")
    a_n = sum(1 for *_, x, y in pairs if x == "N" and y == "N")
    d1 = sum(1 for *_, x, y in pairs if x == "C" and y == "N")
    d2 = sum(1 for *_, x, y in pairs if x == "N" and y == "C")
    po = (a_c + a_n) / n
    p1c = (a_c + d1) / n
    p2c = (a_c + d2) / n
    pe = p1c * p2c + (1 - p1c) * (1 - p2c)
    kappa = (po - pe) / (1 - pe) if pe < 1 else 0.0
    out = {"n": n, "confusion": {"both_C": a_c, "both_N": a_n, "mine_C_audit_N": d1, "mine_N_audit_C": d2},
           "raw_agreement": round(po, 4), "cohen_kappa": round(kappa, 4),
           "disagreements": [{"pos": p, "batch": b, "idx": i, "tier": t, "mine": x, "audit": y}
                             for p, b, i, t, x, y in pairs if x != y]}
    json.dump(out, open(os.path.join(REC, "独立审查-一致性.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n== 站点复核 ==", json.dumps(out["confusion"], ensure_ascii=False),
          f"raw={po:.1%} kappa={kappa:.3f} (n={n})")
    for d in out["disagreements"]:
        print("  ", d)


if __name__ == "__main__":
    main()
