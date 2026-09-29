# -*- coding: utf-8 -*-
"""P1b 第二标注：从 150 站点中分层抽 60（tier 各 20，seed 777），生成盲标注材料
（不含任何已有标签；编号 1..60 与原始 idx 的映射单独保存）

输出:
  C:\\Users\\Administrator\\AppData\\Local\\Temp\\opencode\\p1b_subset_dump.txt
  实验记录/P1b-第二标注-映射.json
"""
import json
import os
import random

REC = r"F:\文献\AgentOps\实验记录"
SAMPLE = os.path.join(REC, "P1b-金标准样本.json")
DUMP = r"C:\Users\Administrator\AppData\Local\Temp\opencode\p1b_subset_dump.txt"
MAP = os.path.join(REC, "P1b-第二标注-映射.json")
SRC_ROOT = r"F:\文献\AgentOps\代码\third_party\vllm-v0.30.0"
SEED = 777
PER_TIER = 20
CTX = 4


def main():
    sample = json.load(open(SAMPLE, encoding="utf-8"))["sites"]
    by_tier = {1: [], 2: [], 3: []}
    for i, s in enumerate(sample, 1):
        by_tier[s["tier"]].append(i)

    rng = random.Random(SEED)
    picked = []
    for t in (1, 2, 3):
        picked += sorted(rng.sample(by_tier[t], min(PER_TIER, len(by_tier[t]))))

    lines_cache = {}

    def lines_of(rel):
        if rel not in lines_cache:
            try:
                lines_cache[rel] = open(os.path.join(SRC_ROOT, rel), encoding="utf-8").read().splitlines()
            except Exception:
                lines_cache[rel] = None
        return lines_cache[rel]

    mapping = {}
    with open(DUMP, "w", encoding="utf-8") as out:
        out.write("P1b 第二标注材料（60 站点，盲标：无任何既有标签）\n")
        out.write("判定口径见任务说明；对每条给出 C 或 N（U 仅限确实无法判断）\n")
        out.write("=" * 96 + "\n")
        for pos, idx in enumerate(picked, 1):
            s = sample[idx - 1]
            mapping[str(pos)] = idx
            out.write(f'[{pos}/60] {s["file"]}:{s["line"]}  (kind={s["kind"]}, tier={s["tier"]})\n')
            out.write(f'  matched_params: {s.get("matched_params")}\n')
            out.write(f'  condition: {(s.get("condition") or "")[:240]}\n')
            if s.get("message"):
                out.write(f'  message: {s["message"][:200]}\n')
            arr = lines_of(s["file"])
            if arr is None:
                out.write("  !! source unreadable\n\n")
                continue
            lo, hi = max(1, s["line"] - CTX), min(len(arr), s["line"] + CTX)
            for n in range(lo, hi + 1):
                mark = ">>" if n == s["line"] else "  "
                out.write(f'   {mark}{n:5d}| {arr[n-1][:150]}\n')
            out.write("\n")

    json.dump({"seed": SEED, "per_tier": PER_TIER, "mapping": mapping},
              open(MAP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"picked={len(picked)} -> {DUMP}")
    print(f"mapping -> {MAP}")


if __name__ == "__main__":
    main()
