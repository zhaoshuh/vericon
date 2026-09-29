# -*- coding: utf-8 -*-
"""解析 P4 扫描输出：提取每个 !! fail 段落的关键错误行"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"C:\Users\Administrator\.local\share\opencode\shell\2d71e05a1c1723d7e4033dd453f29f3c3d6f78af\sh_0e18f39b0001ICdcqljnhcExjE.out"
text = open(p, encoding="utf-8", errors="replace").read()
# 以 study 开始标记分段
blocks = re.split(r"(=== p4 [^\n]*===)", text)
cur_head = None
for i, b in enumerate(blocks):
    if b.startswith("=== p4"):
        cur_head = b.strip()
        continue
    if "!! fail" in b and cur_head:
        # 找 Traceback / Error 行
        errs = [l.strip() for l in b.splitlines()
                if re.search(r"(Error|Exception|Traceback|assert)", l) and len(l.strip()) > 0]
        print("###", cur_head)
        for e in errs[-6:]:
            print("   ", e[:200])
        print()
