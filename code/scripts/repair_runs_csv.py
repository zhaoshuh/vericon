# -*- coding: utf-8 -*-
"""修复 runs.csv 的非法字节（并发写损坏），并报告上下文"""
import sys

p = r"F:\文献\AgentOps\实验记录\runs.csv"
raw = open(p, "rb").read()
print("size:", len(raw))
try:
    raw.decode("utf-8")
    print("utf-8 OK")
except UnicodeDecodeError as e:
    print("decode error:", e)
    lo, hi = max(0, e.start - 120), min(len(raw), e.end + 120)
    print("context bytes:", raw[lo:hi])
    print("context repr:", repr(raw[lo:hi]))

text = raw.decode("utf-8", errors="replace")
n_bad = text.count("\ufffd")
print("replacement chars:", n_bad)
open(p, "w", encoding="utf-8-sig", newline="").write(text)
print("repaired ->", p)

# 同时检查 runs.jsonl
p2 = r"F:\文献\AgentOps\实验记录\runs.jsonl"
raw2 = open(p2, "rb").read()
try:
    raw2.decode("utf-8")
    print("runs.jsonl utf-8 OK")
except UnicodeDecodeError as e:
    print("runs.jsonl decode error:", e)
    text2 = raw2.decode("utf-8", errors="replace")
    open(p2, "w", encoding="utf-8").write(text2)
    print("runs.jsonl repaired, replacements:", text2.count("\ufffd"))
