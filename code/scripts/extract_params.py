# -*- coding: utf-8 -*-
"""S3 · vLLM 参数清单抽取（静态 AST，零依赖）

产出: 实验记录/参数清单.json
用法: python extract_params.py [vllm_src_root] [out_json]

设计约束（与项目硬约束对齐）：
- 每个参数必须带源码证据（file:line + 原始代码片段）
- 抽取 config 类字段 + EngineArgs 字段 + CLI flag，三者可互相映射
- 版本信息（tag/commit）写入 meta，供跨版本对比（Paper 2）
"""
import ast
import json
import os
import sys
from datetime import datetime, timezone

ROOT_DEFAULT = r"F:\文献\AgentOps\代码\third_party\vllm-v0.30.0"
OUT_DEFAULT = r"F:\文献\AgentOps\实验记录\参数清单.json"
ENGINE_VERSION = "v0.30.0"
ENGINE_COMMIT = "ced6857afa0ea7b2e3f0846a62e1394e90f15607"

# 关注的字段名元数据（pydantic Field / Annotated[..., Field(...)]）
META_KEYS = ("ge", "gt", "le", "lt", "multiple_of", "min_length", "max_length", "pattern")


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def unparse(node):
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparse-error>"


def extract_field_meta(value_node):
    """从 Field(...) 或 Annotated[..., Field(...)] 中抽取范围/枚举元数据"""
    meta = {}
    if value_node is None:
        return meta
    calls = []
    if isinstance(value_node, ast.Call):
        calls.append(value_node)
    # Annotated[T, Field(...)]
    if isinstance(value_node, ast.Subscript):
        sl = value_node.slice
        if isinstance(sl, ast.Tuple):
            for el in sl.elts:
                if isinstance(el, ast.Call):
                    calls.append(el)
    for call in calls:
        fname = unparse(call.func) if not isinstance(call.func, ast.Name) else call.func.id
        if fname not in ("Field",):
            continue
        for kw in call.keywords:
            if kw.arg in META_KEYS:
                meta[kw.arg] = unparse(kw.value)
            elif kw.arg == "description" and isinstance(kw.value, ast.Constant):
                meta["description"] = str(kw.value.value)[:300]
            elif kw.arg == "default":
                meta["_default_expr"] = unparse(kw.value)[:200]
    return meta


def walk_enclosing(tree):
    """构建 parent 映射，便于回溯所属类/函数"""
    parent = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
    return parent


def enclosing_class(tree, parent, node):
    cur = node
    while cur in parent:
        cur = parent[cur]
        if isinstance(cur, ast.ClassDef):
            return cur.name
    return None


def iter_assignments(cls_node):
    """产出类体内的字段定义节点（AnnAssign / Assign）"""
    for stmt in cls_node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            yield stmt, stmt.target.id, unparse(stmt.annotation), stmt.value
        elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            name = stmt.targets[0].id
            if name.startswith("_"):
                continue
            yield stmt, name, None, stmt.value


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT_DEFAULT
    out = sys.argv[2] if len(sys.argv) > 2 else OUT_DEFAULT
    pkg_name = sys.argv[3] if len(sys.argv) > 3 else "vllm"
    version_label = sys.argv[4] if len(sys.argv) > 4 else ENGINE_VERSION
    pkg = os.path.join(root, pkg_name)

    params = []
    cli_flags = []
    files_scanned = 0
    files_failed = []

    for dirpath, dirnames, filenames in os.walk(pkg):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "tests", "benchmarks", "examples")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root).replace("\\", "/")
            try:
                text = read_text(path)
                tree = ast.parse(text, filename=path)
            except Exception:
                files_failed.append(rel)
                continue
            files_scanned += 1
            parent = walk_enclosing(tree)
            src_lines = text.splitlines()

            for node in ast.walk(tree):
                # 1) 类字段
                if isinstance(node, ast.ClassDef):
                    for stmt, name, ann, value in iter_assignments(node):
                        if name.startswith("_"):
                            continue
                        meta = extract_field_meta(value)
                        default = None
                        if value is not None and not (isinstance(value, ast.Call) and unparse(value.func).endswith("Field")):
                            default = unparse(value)[:200]
                        if meta.get("_default_expr"):
                            default = meta.pop("_default_expr")
                        params.append({
                            "name": name,
                            "class": node.name,
                            "type": ann,
                            "default": default,
                            "field_meta": meta,
                            "file": rel,
                            "line": stmt.lineno,
                            "evidence": (src_lines[stmt.lineno - 1].strip()[:240] if stmt.lineno - 1 < len(src_lines) else ""),
                            "origin": "config" if rel.startswith("vllm/config/") else ("engine_args" if "arg_utils" in rel else "other"),
                        })
                # 2) CLI flags: add_argument("--x", ...)
                if isinstance(node, ast.Call):
                    fname = ""
                    if isinstance(node.func, ast.Attribute):
                        fname = node.func.attr
                    elif isinstance(node.func, ast.Name):
                        fname = node.func.id
                    if fname == "add_argument" and node.args:
                        a0 = node.args[0]
                        if isinstance(a0, ast.Constant) and isinstance(a0.value, str) and a0.value.startswith("--"):
                            help_txt, dest = "", None
                            for kw in node.keywords:
                                if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                                    help_txt = str(kw.value.value)[:240]
                                if kw.arg == "dest" and isinstance(kw.value, ast.Constant):
                                    dest = kw.value.value
                            if not dest:
                                # 从 flag 推导 dest：--max-num-seqs → max_num_seqs
                                dest = a0.value.lstrip("-").replace("-", "_")
                            cli_flags.append({
                                "flag": a0.value,
                                "dest": dest,
                                "help": help_txt,
                                "file": rel,
                                "line": node.lineno,
                            })

    # 去重（同名同文件同行）
    seen = set()
    uniq_params = []
    for p in params:
        key = (p["name"], p["class"], p["file"], p["line"])
        if key in seen:
            continue
        seen.add(key)
        uniq_params.append(p)
    uniq_params.sort(key=lambda p: (p["file"], p["line"]))

    result = {
        "meta": {
            "engine": pkg_name.split("/")[-1],
            "version": version_label,
            "commit": ENGINE_COMMIT,
            "source_root": root,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "files_scanned": files_scanned,
            "files_failed": files_failed[:20],
        },
        "counts": {
            "params_total": len(uniq_params),
            "params_config": sum(1 for p in uniq_params if p["origin"] == "config"),
            "params_engine_args": sum(1 for p in uniq_params if p["origin"] == "engine_args"),
            "cli_flags": len(cli_flags),
            "classes": len({p["class"] for p in uniq_params}),
        },
        "params": uniq_params,
        "cli_flags": cli_flags,
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result["counts"], ensure_ascii=False))
    print(f"files_scanned={files_scanned} -> {out}")


if __name__ == "__main__":
    main()
