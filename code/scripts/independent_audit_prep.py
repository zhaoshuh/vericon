# -*- coding: utf-8 -*-
"""独立审查（AI 角色）材料准备：
A) 约束对抗性审查：从 716 扩展图抽 30 条（seed 20260928，分层：confirmed 优先 + 类型多样）
B) 金标准站点盲标复核：从 300 站点抽 30 条（两批各 15，seed 20260928）

输出：
  实验记录/独立审查-约束样本.json + 转储 独立审查-约束转储.txt
  实验记录/独立审查-站点样本.json + 转储 独立审查-站点转储.txt
"""
import json
import os
import random

REC = r"F:\文献\AgentOps\实验记录"
GRAPH = os.path.join(REC, "约束图-v1-ext.json")
SRC_ROOT = r"F:\文献\AgentOps\代码\third_party\vllm-v0.30.0"
OUT_CON = os.path.join(REC, "独立审查-约束样本.json")
OUT_SITE = os.path.join(REC, "独立审查-站点样本.json")
DUMP_CON = os.path.join(REC, "独立审查-约束转储.txt")
DUMP_SITE = os.path.join(REC, "独立审查-站点转储.txt")
SEED = 20260928
CTX = 3


def lines_of(rel, cache):
    if rel not in cache:
        try:
            cache[rel] = open(os.path.join(SRC_ROOT, rel), encoding="utf-8").read().splitlines()
        except Exception:
            cache[rel] = None
    return cache[rel]


def main():
    rng = random.Random(SEED)

    # ---- A) 约束样本（30 条）----
    g = json.load(open(GRAPH, encoding="utf-8"))
    nodes = g["nodes"]
    confirmed = [n for n in nodes if (n.get("validation") or {}).get("status") in ("confirmed", "confirmed_cross_model")]
    others = [n for n in nodes if n not in confirmed]
    # 18 条 confirmed + 12 条其他（类型多样性）
    picked = rng.sample(confirmed, min(18, len(confirmed))) if confirmed else []
    by_type = {}
    for n in others:
        by_type.setdefault(n.get("type"), []).append(n)
    for t, pool in sorted(by_type.items()):
        if len(picked) >= 30:
            break
        picked.append(rng.choice(pool))
    while len(picked) < 30 and others:
        cand = rng.choice(others)
        if cand not in picked:
            picked.append(cand)
    json.dump({"seed": SEED, "n": len(picked), "sampled": picked},
              open(OUT_CON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    cache = {}
    with open(DUMP_CON, "w", encoding="utf-8") as out:
        out.write("约束对抗性审查材料（30 条）——目标：逐条尝试证伪（找反例/例外/证据不符）\n")
        out.write("=" * 96 + "\n")
        for i, c in enumerate(picked, 1):
            out.write(f'[{i}/30] {c.get("id")}  type={c.get("type")}  scope={c.get("scope")}\n')
            out.write(f'  expr: {c.get("expr")}\n')
            out.write(f'  mechanism: {(c.get("mechanism") or "")[:200]}\n')
            v = c.get("validation") or {}
            out.write(f'  validation: {v.get("status")}\n')
            for e in c.get("evidence") or []:
                rel, line = e.get("file"), e.get("line")
                out.write(f'  --- {rel}:{line}  snippet={e.get("snippet")!r}\n')
                arr = lines_of(rel, cache)
                if arr is None:
                    out.write("      !! 文件读取失败\n")
                    continue
                lo, hi = max(1, line - CTX), min(len(arr), line + CTX)
                for n in range(lo, hi + 1):
                    mark = ">>" if n == line else "  "
                    out.write(f'   {mark}{n:5d}| {arr[n-1][:150]}\n')
            out.write("\n")

    # ---- B) 站点样本（30 条：两批各 15）----
    s1 = json.load(open(os.path.join(REC, "P1b-金标准样本.json"), encoding="utf-8"))["sites"]
    s2 = json.load(open(os.path.join(REC, "P1b-金标准样本2.json"), encoding="utf-8"))["sites"]
    picks = [(1, i, s1[i - 1]) for i in sorted(rng.sample(range(1, len(s1) + 1), 15))] + \
            [(2, i, s2[i - 1]) for i in sorted(rng.sample(range(1, len(s2) + 1), 15))]
    json.dump({"seed": SEED, "n": len(picks),
               "items": [{"batch": b, "idx": i, "file": s["file"], "line": s["line"], "tier": s["tier"],
                          "kind": s["kind"], "condition": s.get("condition"), "message": s.get("message"),
                          "matched_params": s.get("matched_params")} for b, i, s in picks]},
              open(OUT_SITE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    with open(DUMP_SITE, "w", encoding="utf-8") as out:
        out.write("金标准站点盲标复核材料（30 条）——目标：独立判定 C/N（不参考任何既有标签）\n")
        out.write("=" * 96 + "\n")
        for i, (b, idx, s) in enumerate(picks, 1):
            out.write(f'[{i}/30] batch={b} idx={idx}  {s["file"]}:{s["line"]}  (kind={s["kind"]}, tier={s["tier"]})\n')
            out.write(f'  matched_params: {s.get("matched_params")}\n')
            out.write(f'  condition: {(s.get("condition") or "")[:220]}\n')
            if s.get("message"):
                out.write(f'  message: {s["message"][:180]}\n')
            arr = lines_of(s["file"], cache)
            if arr is None:
                out.write("  !! source unreadable\n\n")
                continue
            lo, hi = max(1, s["line"] - CTX), min(len(arr), s["line"] + CTX)
            for n in range(lo, hi + 1):
                mark = ">>" if n == s["line"] else "  "
                out.write(f'   {mark}{n:5d}| {arr[n-1][:150]}\n')
            out.write("\n")

    print(f"constraints={len(picked)} -> {OUT_CON} / {DUMP_CON}")
    print(f"sites={len(picks)} -> {OUT_SITE} / {DUMP_SITE}")


if __name__ == "__main__":
    main()
