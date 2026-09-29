# -*- coding: utf-8 -*-
"""S3 · 合并各模块约束 JSON → 约束图.json，并做一致性校验

输入:  实验记录/S3_parts/*.json   （每个模块一个，由 sub-agent 产出）
      实验记录/参数清单.json      （参数名白名单）
输出:  实验记录/约束图.json
用法:  python merge_constraints.py [parts_dir] [param_list_json] [out_json] [vllm_src_root]

一致性校验（不合格的约束进 "rejected" 而非静默丢弃）：
  R1 参数名存在性：params 中每个名字能在参数清单里找到（不区分 class）
  R2 证据存在性：evidence 的 file 存在、line 在文件行数内
  R3 片段真实性：snippet（前 40 字符）能在 evidence 行原文中找到
  R4 expr 非空且包含至少一个参数名
"""
import glob
import json
import os
import sys

DEFAULT_PARTS = r"F:\文献\AgentOps\实验记录\S3_parts"
DEFAULT_PARAMS = r"F:\文献\AgentOps\实验记录\参数清单.json"
DEFAULT_OUT = r"F:\文献\AgentOps\实验记录\约束图.json"
DEFAULT_SRC = r"F:\文献\AgentOps\代码\third_party\vllm-v0.30.0"

src_lines_cache = {}


def file_lines(src_root, rel):
    key = rel
    if key not in src_lines_cache:
        path = os.path.join(src_root, rel)
        try:
            with open(path, encoding="utf-8") as f:
                src_lines_cache[key] = f.read().splitlines()
        except Exception:
            src_lines_cache[key] = None
    return src_lines_cache[key]


def check(constraint, param_names, src_root):
    problems = []
    params = constraint.get("params") or []
    for p in params:
        if p not in param_names:
            problems.append(f"R1 参数名不在清单: {p}")

    evid = constraint.get("evidence") or []
    if not evid:
        problems.append("R2 无证据")
    for e in evid:
        rel, line = e.get("file"), e.get("line")
        if not rel or not line:
            problems.append("R2 证据缺 file/line")
            continue
        lines = file_lines(src_root, rel)
        if lines is None:
            problems.append(f"R2 文件不存在: {rel}")
            continue
        if not (1 <= line <= len(lines)):
            problems.append(f"R2 行号越界: {rel}:{line}")
            continue
        snippet = (e.get("snippet") or "").strip()
        if snippet:
            probe = snippet[:40]
            if probe and probe not in lines[line - 1]:
                problems.append(f"R3 片段与原文不符: {rel}:{line}")

    if not (constraint.get("expr") or "").strip():
        problems.append("R4 expr 为空")
    elif params and not any(p in constraint["expr"] for p in params):
        problems.append("R4 expr 未引用声明参数")

    return problems


def main():
    parts_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PARTS
    params_json = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PARAMS
    out_json = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUT
    src_root = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_SRC

    param_names = set()
    with open(params_json, encoding="utf-8") as f:
        plist = json.load(f)
    for p in plist.get("params", []):
        param_names.add(p["name"])
    for c in plist.get("cli_flags", []):
        if c.get("dest"):
            param_names.add(c["dest"])

    merged = []
    rejected = []
    dropped_log = []
    seen = set()
    for part_path in sorted(glob.glob(os.path.join(parts_dir, "*.json"))):
        try:
            with open(part_path, encoding="utf-8") as f:
                part = json.load(f)
        except Exception as ex:
            rejected.append({"source": os.path.basename(part_path), "reason": f"JSON 解析失败: {ex}"})
            continue
        module = part.get("module") or os.path.basename(part_path).replace(".json", "")
        for c in part.get("constraints", []):
            c["scope"] = c.get("scope") or module
            problems = check(c, param_names, src_root)
            if problems:
                rejected.append({"source": os.path.basename(part_path), "constraint": c, "problems": problems})
                continue
            key = (c.get("expr"), tuple(sorted(c.get("params") or [])), c.get("scope"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(c)
        for d in part.get("dropped", []) or []:
            dd = dict(d)
            dd["module"] = module
            dropped_log.append(dd)

    merged.sort(key=lambda c: (c.get("scope") or "", c.get("expr") or ""))

    # 跨模块去重：同 (expr, params) 视为同一约束 → 保留证据更多/置信度更高者
    def _rank(c):
        n_ev = len(c.get("evidence") or [])
        conf = float((c.get("extraction") or {}).get("confidence") or 0.0)
        return (n_ev, conf)

    best_by_key = {}
    for c in merged:
        key = ((c.get("expr") or "").strip(), tuple(sorted(c.get("params") or [])))
        if key not in best_by_key or _rank(c) > _rank(best_by_key[key]):
            best_by_key[key] = c
    merged = list(best_by_key.values())
    merged.sort(key=lambda c: (c.get("scope") or "", c.get("expr") or ""))

    for i, c in enumerate(merged, 1):
        c["id"] = f"C{i:03d}"
        c.setdefault("validation", {"status": "unverified", "method": None, "run_id": None, "note": None})

    by_type, by_scope = {}, {}
    for c in merged:
        by_type[c.get("type", "?")] = by_type.get(c.get("type", "?"), 0) + 1
        by_scope[c.get("scope", "?")] = by_scope.get(c.get("scope", "?"), 0) + 1

    src_meta = {}
    try:
        with open(params_json, encoding="utf-8") as f:
            src_meta = json.load(f).get("meta", {})
    except Exception:
        pass

    result = {
        "meta": {
            "engine": src_meta.get("engine", "vllm"),
            "version": src_meta.get("version", "unknown"),
            "commit": src_meta.get("commit", "unknown"),
            "merged_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "parts_dir": parts_dir,
        },
        "stats": {
            "total": len(merged),
            "with_evidence": sum(1 for c in merged if c.get("evidence")),
            "by_type": by_type,
            "by_scope": by_scope,
            "rejected": len(rejected),
            "dropped_by_agent": len(dropped_log),
        },
        "nodes": merged,
        "rejected": rejected,
        "dropped_by_agent": dropped_log,
    }
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result["stats"], ensure_ascii=False)[:600])
    print(f"-> {out_json}")


if __name__ == "__main__":
    main()
