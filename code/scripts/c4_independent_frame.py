# -*- coding: utf-8 -*-
"""C4 v2 · 独立抽样框捕获率（修正：evidence 为 dict 列表；抽样限于 vllm/ ；过滤收紧到语句本体）"""
import ast
import json
import os
import random
import re
from collections import Counter

ROOT = "/mnt/f/文献/AgentOps/代码/third_party/vllm-v0.30.0"
PARAMS = "/mnt/f/文献/AgentOps/实验记录/参数清单.json"
GRAPH = "/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json"
OUT_DIR = "/mnt/f/文献/AgentOps/实验记录/C4-独立抽样框"
SAMPLE_N = 150
SEED = 20260929

pd = json.load(open(PARAMS, encoding="utf-8"))
eng_names, all_names = set(), set()
for p in pd.get("params", []):
    nm = p.get("name")
    if not nm:
        continue
    all_names.add(nm)
    if p.get("origin") in ("config", "engine_args"):
        eng_names.add(nm)
for f in pd.get("cli_flags", []):
    if f.get("dest"):
        eng_names.add(f["dest"])
        all_names.add(f["dest"])
san = lambda S: {n for n in S if len(n) >= 4 and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n)}
eng_names, all_names = san(eng_names), san(all_names)
pat_eng = re.compile(r"\b(" + "|".join(sorted(eng_names, key=len, reverse=True)) + r")\b")
pat_all = re.compile(r"\b(" + "|".join(sorted(all_names, key=len, reverse=True)) + r")\b")
print(f"名称表: engine={len(eng_names)} all={len(all_names)}")

gd = json.load(open(GRAPH, encoding="utf-8"))
nodes = gd["nodes"]


def ev_pairs(ev):
    if isinstance(ev, dict):
        yield ev.get("file"), ev.get("line")
    elif isinstance(ev, list):
        for it in ev:
            yield from ev_pairs(it)
    elif isinstance(ev, str):
        m = re.search(r"([\w./\\-]+\.py):(\d+)", ev)
        if m:
            yield m.group(1).replace("\\", "/"), int(m.group(2))


cap_index = {}
for n in nodes:
    for f, l in ev_pairs(n.get("evidence")):
        if f and l:
            cap_index.setdefault(f.replace("\\", "/").lstrip("./"), []).append((int(l), n.get("id")))
print(f"约束集: {len(nodes)} 节点; 索引文件数: {len(cap_index)}")

all_files = []
for dirpath, _, filenames in os.walk(os.path.join(ROOT, "vllm")):
    for fn in filenames:
        if fn.endswith(".py"):
            all_files.append(os.path.join(dirpath, fn))
print(f"vllm/ .py 文件: {len(all_files)}")

rng = random.Random(SEED)
sample = rng.sample(all_files, min(SAMPLE_N, len(all_files)))

sites = []
for fp in sample:
    rel = os.path.relpath(fp, ROOT).replace("\\", "/")
    try:
        src = open(fp, encoding="utf-8", errors="replace").read()
        tree = ast.parse(src)
    except Exception:
        continue
    lines = src.splitlines()
    for node in ast.walk(tree):
        kind = None
        if isinstance(node, ast.Assert):
            kind = "assert"
        elif isinstance(node, ast.Raise) and node.exc is not None:
            kind = "raise"
        if kind is None:
            continue
        seg = ast.get_source_segment(src, node)
        if seg is None:
            lo = max(0, node.lineno - 2)
            hi = min(len(lines), getattr(node, "end_lineno", node.lineno) + 1)
            seg = "\n".join(lines[lo:hi])
        eng_hits = sorted(set(m.group(1) for m in pat_eng.finditer(seg)))
        all_hits = sorted(set(m.group(1) for m in pat_all.finditer(seg)))
        if not eng_hits and not all_hits:
            continue
        matched_id, matched_exact = None, False
        for (cl, cid) in cap_index.get(rel, []):
            if abs(cl - node.lineno) <= 1:
                matched_id, matched_exact = cid, (cl == node.lineno)
                break
        sites.append({
            "file": rel, "line": node.lineno, "kind": kind,
            "engine_hit": bool(eng_hits), "param_hits": (eng_hits or all_hits)[:6],
            "snippet": seg.strip().splitlines()[0][:170] if seg.strip() else "",
            "captured": matched_id is not None, "exact": matched_exact, "matched_id": matched_id,
            "file_in_index": rel in cap_index,
            "dir_class": ("vllm/config" if rel.startswith("vllm/config") else
                          "vllm/engine" if rel.startswith("vllm/engine") else
                          "vllm/v1" if rel.startswith("vllm/v1") else
                          "vllm/model_executor" if rel.startswith("vllm/model_executor") else "other"),
        })

eng_sites = [s for s in sites if s["engine_hit"]]
n, cap = len(eng_sites), sum(1 for s in eng_sites if s["captured"])
exact = sum(1 for s in eng_sites if s["exact"])
n_allp, cap_allp = len(sites), sum(1 for s in sites if s["captured"])

stats = {
    "frame": {"seed": SEED, "files_sampled": len(sample), "universe_files": len(all_files),
              "criterion": "语句本体（ast source segment）命中名称表"},
    "engine_name_sites": {"n": n, "captured": cap, "capture_rate": round(cap / n, 4) if n else None,
                          "exact": exact},
    "all_param_sites": {"n": n_allp, "captured": cap_allp,
                        "capture_rate": round(cap_allp / n_allp, 4) if n_allp else None},
    "by_dir_class": {},
}
for dc in sorted(set(s["dir_class"] for s in eng_sites)):
    sub = [s for s in eng_sites if s["dir_class"] == dc]
    stats["by_dir_class"][dc] = {"sites": len(sub), "captured": sum(1 for s in sub if s["captured"])}

os.makedirs(OUT_DIR, exist_ok=True)
json.dump({"stats": stats, "sites": sites}, open(os.path.join(OUT_DIR, "frame_sites.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\n=== 结果（engine 名称口径）===")
print(f"抽样 {len(sample)} 文件 → engine-名称站点 {n} → captured {cap} ({cap/n*100:.1f}%)  exact={exact}" if n else "n/a")
print(f"（全参数名称口径：{cap_allp}/{n_allp}）")
for k, v in stats["by_dir_class"].items():
    print(f"  {k}: {v['captured']}/{v['sites']}")

print("\n=== 未捕获（engine 口径）前 14 ===")
for s in [x for x in eng_sites if not x["captured"]][:14]:
    print(f"  [{s['dir_class']}] {s['file']}:{s['line']} ({s['kind']}) {s['snippet'][:110]}")
print("\n=== 已捕获前 6 ===")
for s in [x for x in eng_sites if x["captured"]][:6]:
    print(f"  {s['file']}:{s['line']} -> {s['matched_id']} {'=' if s['exact'] else '±1'}")
print("DONE")
