# -*- coding: utf-8 -*-
"""P1b 标注者间一致性：我方标签 vs 第二标注者（60 站点子集）
输出：实验记录/P1b-标注一致性.json + 追加结果到 P1b-金标准-结果-ext.md 末尾
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REC = r"F:\文献\AgentOps\实验记录"
LABELS = os.path.join(REC, "P1b-标注结果.json")
SECOND = os.path.join(REC, "P1b-第二标注-结果.json")
MAP = os.path.join(REC, "P1b-第二标注-映射.json")
OUT = os.path.join(REC, "P1b-标注一致性.json")
MD = os.path.join(REC, "P1b-金标准-结果-ext.md")


def main():
    mine = {r["idx"]: r["label"] for r in json.load(open(LABELS, encoding="utf-8"))["rows"]}
    mapping = json.load(open(MAP, encoding="utf-8"))["mapping"]
    second = json.load(open(SECOND, encoding="utf-8"))["labels"]
    tiers = {r["idx"]: r["tier"] for r in json.load(open(LABELS, encoding="utf-8"))["rows"]}

    pairs = []
    for pos, idx in mapping.items():
        a = mine.get(idx)
        b = second.get(str(pos), {}).get("label")
        if a in ("C", "N") and b in ("C", "N"):
            pairs.append((idx, tiers[idx], a, b))

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
            agree = sum(1 for x, y in sub if x == y) / len(sub)
            per_tier[t] = {"n": len(sub), "agreement": round(agree, 3)}

    out = {
        "n": n, "confusion": {"both_C": a_c, "both_N": a_n, "mine_C_second_N": d1, "mine_N_second_C": d2},
        "raw_agreement": round(po, 4), "cohen_kappa": round(kappa, 4),
        "second_C_rate": round(p2c, 4), "mine_C_rate": round(p1c, 4),
        "per_tier": per_tier,
        "disagreements": [{"idx": i, "tier": t, "mine": x, "second": y} for i, t, x, y in pairs if x != y],
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    md_add = [
        "",
        "## 标注者间一致性（第二标注者盲标 60 站点）",
        "",
        f"- 子集：分层 20/20/20（seed 777），双盲独立判定；**原始一致率 {po:.1%}**，**Cohen's κ = {kappa:.3f}**",
        f"- 混淆：both C = {a_c}；both N = {a_n}；我方 C/二标 N = {d1}；我方 N/二标 C = {d2}",
        "- 分层一致率：" + "；".join(f"tier{t} {v['agreement']:.0%}（n={v['n']}）" for t, v in per_tier.items()),
        f"- 分歧清单：{len(out['disagreements'])} 条（详见 `P1b-标注一致性.json`）",
        "",
        "*第二标注者：独立模型实例、盲标（未接触既有标签）；口径与主标注完全一致（见输入材料首段）。*",
    ]
    with open(MD, "a", encoding="utf-8") as f:
        f.write("\n".join(md_add) + "\n")

    print(json.dumps(out, ensure_ascii=False, indent=1)[:1200])
    print("->", OUT)


if __name__ == "__main__":
    main()
