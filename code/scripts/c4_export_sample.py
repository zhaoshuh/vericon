# -*- coding: utf-8 -*-
"""C4 第三步：导出 50 站点人工裁定样本 + 生成候选 CSV"""
import json
import random
from collections import Counter

d = json.load(open("/mnt/f/文献/AgentOps/实验记录/C4-独立抽样框/frame_sites.json", encoding="utf-8"))
eng = [s for s in d["sites"] if s["engine_hit"]]
print("engine-hit sites:", len(eng))
rng = random.Random(777)
sample = rng.sample(eng, min(50, len(eng)))
print("\n=== 裁定样本（50）===")
for i, s in enumerate(sample):
    snip = s["snippet"].replace("\n", " ")
    print(f"{i:02d}|{s['file']}:{s['line']}|{s['kind']}|cap={int(s['captured'])}|hits={','.join(s['param_hits'][:4])}|{snip[:120]}")
json.dump(sample, open("/mnt/f/文献/AgentOps/实验记录/C4-独立抽样框/adjudication_sample.json", "w",
          encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nSAMPLE SAVED")
