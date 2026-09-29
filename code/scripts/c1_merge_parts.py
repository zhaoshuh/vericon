# -*- coding: utf-8 -*-
"""C1 第三步：合并三批盲标 + 适配导入脚本措辞 + 运行导入"""
import csv
import os

C1 = "/mnt/f/文献/AgentOps/实验记录/C1-人类盲标"
# 1) 合并
rows = []
for i in (1, 2, 3):
    p = os.path.join(C1, f"c1_part{i}.csv")
    with open(p, encoding="utf-8-sig") as fh:
        part = list(csv.DictReader(fh))
    print(f"part{i}: {len(part)} 行, verdicts:", {v: sum(1 for r in part if r['verdict'].strip().upper()[:1] == v) for v in 'YNU'})
    rows += part
assert len(rows) == 150

with open(os.path.join(C1, "c1_results.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "verdict", "note", "file", "line", "tier"])
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in ["id", "verdict", "note", "file", "line", "tier"]})
print("merged ->c1_results.csv:", len(rows))

# 2) 适配导入脚本措辞（human → 独立盲标(AI)）
p = "/mnt/f/文献/AgentOps/代码/scripts/c1_import_results.py"
t = open(p, encoding="utf-8").read()
reps = [
    ('"""C1 · 人类标注回传导入', '"""C1 · 独立盲标回传导入（AI 第三遍；非人类）'),
    ("打印\n", "打印\n"),
    ('print("\\n人类标签下的召回（对照论文 71.9%/87.2%）：")', 'print("\\n独立盲标(AI第三遍)标签下的召回（对照论文 71.9%/87.2%）：")'),
    ('"human": v,', '"pass": v,'),
    ('"human_recall": {"equal_weight"', '"pass_recall": {"equal_weight"'),
]
for o, n in reps:
    if o in t:
        t = t.replace(o, n)
    else:
        print("  (miss)", o[:50])
open(p, "w", encoding="utf-8", newline="").write(t)
print("import 脚本措辞已更新")
