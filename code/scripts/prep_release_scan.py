# -*- coding: utf-8 -*-
"""发布前：体量测算 + 敏感内容扫描（只报计数，不打印敏感值）"""
import os
import re

AP = "/mnt/f/文献/AgentOps"

def size_of(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    tot = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                tot += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return tot

print("== 体量（MB）==")
for p in ["实验记录", "代码/agentops", "代码/scripts", "论文/latex", "论文Q4/仓库/llm-serving-config-constraints"]:
    print(f"  {p}: {size_of(os.path.join(AP, p))/1e6:.1f}")

print("\n== 实验记录 中最大的 15 个文件（MB）==")
rows = []
for root, _, files in os.walk(os.path.join(AP, "实验记录")):
    for f in files:
        p = os.path.join(root, f)
        try:
            rows.append((os.path.getsize(p), os.path.relpath(p, os.path.join(AP, "实验记录"))))
        except OSError:
            pass
for s, r in sorted(rows, reverse=True)[:15]:
    print(f"  {s/1e6:8.2f}  {r}")

PATS = {
    "token/sk": re.compile(r"sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_"),
    "password": re.compile(r"(?i)passwo?rd\s*[:=]\s*\S+"),
    "userprofile": re.compile(r"C:\\\\?Users\\\\?[A-Za-z]"),
    "other_email": re.compile(r"[A-Za-z0-9._%+-]+@(?!163\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "advisor_cn": re.compile(r"导师"),
    "phone": re.compile(r"\b1[3-9]\d{9}\b"),
}
print("\n== 敏感内容扫描（文件计数）==")
hits = {k: [] for k in PATS}
for base in ["实验记录", "代码/agentops", "代码/scripts", "论文/latex"]:
    for root, _, files in os.walk(os.path.join(AP, base)):
        for f in files:
            p = os.path.join(root, f)
            if os.path.getsize(p) > 4_000_000:
                continue
            try:
                t = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for k, rx in PATS.items():
                if rx.search(t):
                    hits[k].append(os.path.relpath(p, AP))
for k, v in hits.items():
    print(f"  {k}: {len(v)} 个文件", v[:4])
