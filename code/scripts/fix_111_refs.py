# -*- coding: utf-8 -*-
"""批量修正报告中的 '111 条' → '113 条'（跨模型新增并入后的口径同步）"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"F:\文献\AgentOps\实验记录"
FILES = [
    os.path.join(ROOT, "S4-验证报告.md"),
    os.path.join(ROOT, "S5-报告.md"),
    os.path.join(ROOT, "S6-真机锚点-报告.md"),
    os.path.join(ROOT, "导师复核意见-2026-09-27.md"),
    os.path.join(ROOT, "已验证约束-跨引擎.json"),
]

for path in FILES:
    with io.open(path, encoding="utf-8") as f:
        text = f.read()
    n1 = text.count("111 条")
    n2 = text.count("111/22/22/127")
    if not (n1 or n2):
        print("no change:", os.path.basename(path))
        continue
    text = text.replace("111/22/22/127", "113/22/22/127")
    text = text.replace("111 条", "113 条")
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{os.path.basename(path)}: '111 条' x{n1}, '111/22/22/127' x{n2} -> replaced")
