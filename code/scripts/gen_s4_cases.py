# -*- coding: utf-8 -*-
"""S4 · 由约束自动生成"违反配置"用例（尽力而为，失败不阻塞）

输入: 实验记录/约束图.json, 实验记录/参数清单.json
输出: 实验记录/S4验证/cases.json

思路：对每条约束的表达式（如 a >= b / not(a and b) / if x then y），
在参数取值域上做**固定种子的随机+边界搜索**，找到一个让表达式为假的赋值；
找不到的标 needs_manual（留给人工/S4 人工构造）。
"""
import json
import os
import random
import re
import sys

DEFAULT_GRAPH = r"F:\文献\AgentOps\实验记录\约束图.json"
DEFAULT_PARAMS = r"F:\文献\AgentOps\实验记录\参数清单.json"
DEFAULT_OUT = r"F:\文献\AgentOps\实验记录\S4验证\cases.json"

INT_CANDIDATES = [0, 1, 2, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 1000000]
FLOAT_CANDIDATES = [0.0, 0.1, 0.5, 0.9, 0.95, 1.0, 1.5, 2.0, 16.0, 100.0]


def norm_expr(expr):
    """把 agent 写的表达式归一成可 eval 的近似形式"""
    if not isinstance(expr, str):
        return None
    e = expr.strip()
    e = e.replace("self.", "")
    # 'if X then Y' → 'not (X) or (Y)'
    m = re.match(r"^if\s+(.+?)\s+then\s+(.+)$", e, flags=re.I)
    if m:
        e = f"(not ({m.group(1)})) or ({m.group(2)})"
    # 'unless X' 之类懒处理：放弃
    if re.search(r"[^\w\s\.\(\)\[\]\,\:\'\+\-\*/<>=!%&|^~]", e):
        return None
    return e


def domains_for(params, param_index):
    dom = {}
    for p in params:
        info = param_index.get(p, {})
        t = (info.get("type") or "").lower()
        if "bool" in t or info.get("default") in ("True", "False"):
            dom[p] = [True, False]
        elif "float" in t:
            dom[p] = FLOAT_CANDIDATES
        else:
            dom[p] = INT_CANDIDATES
    return dom


def main():
    graph_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GRAPH
    params_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PARAMS
    out_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUT

    with open(graph_path, encoding="utf-8") as f:
        graph = json.load(f)
    with open(params_path, encoding="utf-8") as f:
        plist = json.load(f)

    index = {}
    for p in plist.get("params", []):
        index.setdefault(p["name"], p)

    rng = random.Random(20260926)
    cases, manual = [], []
    for c in graph.get("nodes", []):
        cid = c.get("id")
        expr = norm_expr(c.get("expr"))
        params = [p for p in (c.get("params") or []) if p in index] or list(c.get("params") or [])
        if not expr or not params:
            manual.append({"id": cid, "expr": c.get("expr"), "reason": "expr 不可解析/参数不在清单"})
            continue
        dom = domains_for(params, index)
        found = None
        for _ in range(4000):
            assign = {p: rng.choice(dom[p]) for p in params}
            try:
                ok = bool(eval(expr, {"__builtins__": {}}, assign))  # noqa: S307 (受控小表达式)
            except Exception:
                found = None
                break
            if not ok:
                found = assign
                break
        if found is None:
            manual.append({"id": cid, "expr": c.get("expr"), "params": params, "reason": "搜索未找到违反赋值"})
        else:
            cases.append({
                "constraint_id": cid,
                "type": c.get("type"),
                "scope": c.get("scope"),
                "expr": c.get("expr"),
                "normalized_expr": expr,
                "params": params,
                "violation_assignment": found,
                "evidence": c.get("evidence"),
                "status": "case_ready",
            })

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"cases": cases, "manual": manual,
                   "counts": {"total": len(graph.get("nodes", [])), "case_ready": len(cases), "needs_manual": len(manual)}},
                  f, ensure_ascii=False, indent=2)
    print(json.dumps({"case_ready": len(cases), "needs_manual": len(manual)}, ensure_ascii=False))
    print(f"-> {out_path}")


if __name__ == "__main__":
    main()
