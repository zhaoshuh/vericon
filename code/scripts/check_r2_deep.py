# -*- coding: utf-8 -*-
"""深查 SCOOT 规则 #2（chunked-prefill ⊥ prefix-caching）在 v0.5.5 / v0.4.2 的源码中是否存在校验
方法：多行窗口（±6 行）同时包含两个 token 的片段全部打印；另查报错消息关键词。
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TP = r"F:\文献\AgentOps\代码\third_party\vllm-versions"

TOK_A = re.compile(r"enable_chunked_prefill")
TOK_B = re.compile(r"enable_prefix_caching")

for ver in ("v0.4.2", "v0.5.5"):
    root = os.path.join(TP, ver)
    print("=" * 90)
    print(f"### {ver}")
    found = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "tests", "benchmarks", "examples")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines):
                if TOK_A.search(line):
                    lo, hi = max(0, i - 6), min(len(lines), i + 7)
                    window = "\n".join(lines[lo:hi])
                    if TOK_B.search(window):
                        found += 1
                        rel = os.path.relpath(path, root).replace("\\", "/")
                        print(f"--- {rel}:{i+1} (窗口内同现) ---")
                        for n in range(lo, hi):
                            mark = ">>" if n == i else "  "
                            print(f"   {mark}{n+1:5d}| {lines[n][:130]}")
                        if found >= 4:
                            break
            if found >= 4:
                break
        if found >= 4:
            break
    if found == 0:
        print("  （±6 行窗口内无任何同现）")
    # 报错消息关键词
    for kw in ("chunked prefill", "prefix caching"):
        hits = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "tests")]
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                try:
                    for i, line in enumerate(open(path, encoding="utf-8", errors="ignore"), 1):
                        if kw in line.lower() and ("not" in line.lower() or "cannot" in line.lower() or "support" in line.lower()):
                            hits.append(f'{os.path.relpath(path, root).replace(chr(92), "/")}:{i}: {line.strip()[:110]}')
                except Exception:
                    pass
        print(f"  [{kw} × not/cannot/support] {len(hits)} 处")
        for h in hits[:5]:
            print("    ", h)
