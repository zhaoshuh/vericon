# -*- coding: utf-8 -*-
"""C4 第四步：强名称过滤 → 引擎候选站点清单（供人工核验）+ 对照组"""
import json
import random

d = json.load(open("/mnt/f/文献/AgentOps/实验记录/C4-独立抽样框/frame_sites.json", encoding="utf-8"))
eng = [s for s in d["sites"] if s["engine_hit"]]

GENERIC = {
    "type", "count", "weight", "dtype", "backend", "config", "model", "host", "rank",
    "linear", "device", "video", "image", "audio", "hidden_size", "head_size", "activation",
    "targets", "cache", "size", "value", "name", "data", "output", "input", "graph",
    "limit", "format", "mode", "state", "status", "kind", "shape", "layer", "layers",
    "token", "tokens", "length", "index", "offset", "step", "start", "end", "time",
    "version", "path", "file", "group", "list", "item", "items", "result", "value",
}
rows = []
for i, s in enumerate(eng):
    strong = [h for h in s["param_hits"] if h not in GENERIC]
    rows.append((i, s, strong))

cand = [(i, s, sh) for (i, s, sh) in rows if sh]
ctrl = [(i, s, sh) for (i, s, sh) in rows if not sh]
print(f"engine-hit={len(eng)}  strong候选={len(cand)}  对照池={len(ctrl)}")

print("\n===== 强名称候选（全部）=====")
for k, (i, s, sh) in enumerate(cand):
    print(f"E{k:02d}|idx{i}|{s['file']}:{s['line']}|cap={int(s['captured'])}|{','.join(sh[:4])}|{s['snippet'][:105]}")

rng = random.Random(4242)
ctrl_s = rng.sample(ctrl, min(15, len(ctrl)))
print("\n===== 对照组（随机 15，检查漏判）=====")
for k, (i, s, sh) in enumerate(ctrl_s):
    print(f"K{k:02d}|idx{i}|{s['file']}:{s['line']}|cap={int(s['captured'])}|{','.join(s['param_hits'][:4])}|{s['snippet'][:105]}")

json.dump({"cand_idx": [i for (i, s, sh) in cand], "ctrl_idx": [i for (i, s, sh) in ctrl_s],
           "ctrl_pool_idx": [i for (i, s, sh) in ctrl]},
          open("/mnt/f/文献/AgentOps/实验记录/C4-独立抽样框/candidates.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nSAVED candidates.json")
