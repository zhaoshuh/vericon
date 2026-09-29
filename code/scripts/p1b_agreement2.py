# -*- coding: utf-8 -*-
"""P1b 第二批标注者间一致性（60 站点：1-20, 51-70, 101-120）"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REC = r"F:\文献\AgentOps\实验记录"
LAB2 = os.path.join(REC, "P1b-标注结果2.json")
SECOND = os.path.join(REC, "P1b-第二标注-结果2.json")
OUT = os.path.join(REC, "P1b-标注一致性2.json")

POS = list(range(1, 21)) + list(range(51, 71)) + list(range(101, 121))


def main():
    mine = {r["idx"]: r for r in json.load(open(LAB2, encoding="utf-8"))["rows"]}
    second = json.load(open(SECOND, encoding="utf-8"))["labels"]

    pairs = []
    for pos in POS:
        a = mine.get(pos, {}).get("label")
        b = second.get(str(pos), {}).get("label")
        if a in ("C", "N") and b in ("C", "N"):
            pairs.append((pos, mine[pos]["tier"], a, b))

    n = len(pairs)
    a_c = sum(1 for _, _, x, y in pairs if x == "C" and y == "C")
    a_n = sum(1 for _, _, x, y in pairs if x == "N" and y == "N")
    d1 = sum(1 for _, _, x, y in pairs if x == "C" and y == "N")
    d2 = sum(1 for _, _, x, y in pairs if x == "N" and y == "C")
    po = (a_c + a_n) / n
    p1c = (a_c + d1) / n
    p2c = (a_c + d2) / n
    pe = p1c * p2c + (1 - p1c) * (1 - p2c)
    kappa = (po - pe) / (1 - pe) if pe < 1 else 0.0

    per_tier = {}
    for t in (1, 2, 3):
        sub = [(x, y) for _, tt, x, y in pairs if tt == t]
        if sub:
            per_tier[t] = {"n": len(sub), "agreement": round(sum(1 for x, y in sub if x == y) / len(sub), 3)}

    out = {
        "n": n,
        "confusion": {"both_C": a_c, "both_N": a_n, "mine_C_second_N": d1, "mine_N_second_C": d2},
        "raw_agreement": round(po, 4), "cohen_kappa": round(kappa, 4),
        "mine_C_rate": round(p1c, 4), "second_C_rate": round(p2c, 4),
        "per_tier": per_tier,
        "disagreements": [{"pos": p, "tier": t, "mine": x, "second": y} for p, t, x, y in pairs if x != y],
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
