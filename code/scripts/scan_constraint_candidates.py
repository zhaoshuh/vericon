# -*- coding: utf-8 -*-
"""S3 · vLLM 约束候选静态扫描（assert / if-raise / Field 元数据）

产出: 实验记录/约束候选_静态.json
用法: python scan_constraint_candidates.py [vllm_src_root] [out_json]

扫描对象（按优先级分层）：
  tier1 = vllm/config/            （配置校验最集中）
  tier2 = vllm/engine/, vllm/v1/engine/, vllm/v1/core/
  tier3 = vllm/ 其余
产物只做"候选"：每条带 file:line + 代码片段；结构化/证伪在后续步骤（agent 审查 + 沙箱）。
"""
import ast
import json
import os
import sys
from datetime import datetime, timezone

ROOT_DEFAULT = r"F:\文献\AgentOps\代码\third_party\vllm-v0.30.0"
OUT_DEFAULT = r"F:\文献\AgentOps\实验记录\约束候选_静态.json"
ENGINE_VERSION = "v0.30.0"

TIER1 = ("vllm/config/",)
TIER2 = ("vllm/engine/", "vllm/v1/engine/", "vllm/v1/core/", "vllm/platforms/")


def tier_of(rel):
    if any(rel.startswith(p) for p in TIER1):
        return 1
    if any(rel.startswith(p) for p in TIER2):
        return 2
    return 3


def unparse(node):
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparse-error>"


def build_parents(tree):
    parent = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
    return parent


def enclosing(parent, node):
    """返回 (class, function) 名"""
    cls = fn = None
    cur = node
    while cur in parent:
        cur = parent[cur]
        if cls is None and isinstance(cur, ast.ClassDef):
            cls = cur.name
        if fn is None and isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn = cur.name
        if cls and fn:
            break
    return cls, fn


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT_DEFAULT
    out = sys.argv[2] if len(sys.argv) > 2 else OUT_DEFAULT
    pkg_name = sys.argv[3] if len(sys.argv) > 3 else "vllm"
    version_label = sys.argv[4] if len(sys.argv) > 4 else ENGINE_VERSION
    pkg = os.path.join(root, pkg_name)

    candidates = []
    files_scanned = 0

    for dirpath, dirnames, filenames in os.walk(pkg):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "tests", "benchmarks", "examples")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root).replace("\\", "/")
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                tree = ast.parse(text, filename=path)
            except Exception:
                continue
            files_scanned += 1
            parent = build_parents(tree)
            lines = text.splitlines()
            t = tier_of(rel)

            def snippet(lineno):
                return lines[lineno - 1].strip()[:240] if 0 < lineno <= len(lines) else ""

            for node in ast.walk(tree):
                # A) assert 语句
                if isinstance(node, ast.Assert):
                    cls, fnn = enclosing(parent, node)
                    candidates.append({
                        "kind": "assert",
                        "tier": t,
                        "file": rel,
                        "line": node.lineno,
                        "class": cls,
                        "function": fnn,
                        "condition": unparse(node.test)[:300],
                        "message": (unparse(node.msg)[:200] if node.msg else None),
                        "evidence": snippet(node.lineno),
                    })
                # B) if <cond>: raise ...
                if isinstance(node, ast.If):
                    raises = [s for s in list(node.body) + list(node.orelse) if isinstance(s, ast.Raise)]
                    if raises:
                        cls, fnn = enclosing(parent, node)
                        for r in raises:
                            exc = None
                            if r.exc is not None:
                                exc = unparse(r.exc.func if isinstance(r.exc, ast.Call) else r.exc)[:80]
                            candidates.append({
                                "kind": "if-raise",
                                "tier": t,
                                "file": rel,
                                "line": r.lineno,
                                "class": cls,
                                "function": fnn,
                                "condition": unparse(node.test)[:300],
                                "exception": exc,
                                "message": (unparse(r.exc.args[0])[:200] if isinstance(r.exc, ast.Call) and r.exc.args else None),
                                "evidence": snippet(r.lineno),
                            })

    candidates.sort(key=lambda c: (c["tier"], c["file"], c["line"]))
    result = {
        "meta": {
            "engine": pkg_name.split("/")[-1],
            "version": version_label,
            "source_root": root,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "files_scanned": files_scanned,
            "note": "静态候选：kind=assert/if-raise；需经 agent 结构化 + 沙箱证伪后才进入约束图",
        },
        "counts": {
            "total": len(candidates),
            "by_kind": {k: sum(1 for c in candidates if c["kind"] == k) for k in ("assert", "if-raise")},
            "by_tier": {t: sum(1 for c in candidates if c["tier"] == t) for t in (1, 2, 3)},
        },
        "candidates": candidates,
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result["counts"], ensure_ascii=False))
    print(f"files_scanned={files_scanned} -> {out}")


if __name__ == "__main__":
    main()
