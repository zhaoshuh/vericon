# -*- coding: utf-8 -*-
"""把 C1 站点包切成 3 批匿名文件（仅保留盲标可见字段，不带任何标签/捕获信息）"""
import json
import os

C1 = "/mnt/f/文献/AgentOps/实验记录/C1-人类盲标"
pack = json.load(open(os.path.join(C1, "sites-pack.json"), encoding="utf-8"))["items"]
assert len(pack) == 150

KEEP = ("id", "tier", "file", "line", "kind", "condition", "exception", "message", "context")
for b in range(3):
    part = pack[b * 50:(b + 1) * 50]
    out = [{k: it.get(k) for k in KEEP} for it in part]
    path = os.path.join(C1, f"c1_batch{b+1}.json")
    json.dump({"n": len(out), "items": out}, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(path, len(out), "items")
# 校验：不含任何标签类字段
allk = set()
for it in pack:
    allk |= set(it.keys())
print("原始字段集合:", sorted(allk))
print("切批字段:", sorted(KEEP))
