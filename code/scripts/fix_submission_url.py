# -*- coding: utf-8 -*-
"""修正投稿入口链接：tse → cs-ieee（Journal 下拉选 Transactions on Software Engineering）"""
import io

LAT = "/mnt/f/文献/AgentOps/论文/latex"
p = f"{LAT}/投稿-提交清单.md"
t = open(p, encoding="utf-8").read()

old = "1. 打开 IEEE TSE 的 ScholarOne：`https://mc.manuscriptcentral.com/tse`（以 TSE 作者指南页面的最新链接为准）"
new = ("1. 打开 **IEEE Computer Society 投稿入口**：`https://mc.manuscriptcentral.com/cs-ieee`\n"
       "2. 在 **Journal 下拉**里选择 **`Transactions on Software Engineering`**（选项列表中第 31 项）\n"
       "   ⚠️ **不要用 `mc.manuscriptcentral.com/tse`**——那是期刊 *Transportation Safety and Environment* 的投稿站（同名缩写，非 IEEE TSE）")
if old in t:
    t = t.replace(old, new)
    print("清单已修正")
else:
    t = t.replace("https://mc.manuscriptcentral.com/tse", "https://mc.manuscriptcentral.com/cs-ieee（Journal 下拉选 Transactions on Software Engineering）")
    print("清单：已做兜底替换")
open(p, "w", encoding="utf-8", newline="").write(t)

# README-投稿包 同步
r = f"{LAT}/README-投稿包.md"
if __import__("os").path.exists(r):
    rt = open(r, encoding="utf-8").read()
    if "mc.manuscriptcentral.com/tse" in rt:
        rt = rt.replace("https://mc.manuscriptcentral.com/tse",
                        "https://mc.manuscriptcentral.com/cs-ieee（Journal 下拉选 Transactions on Software Engineering）")
        open(r, "w", encoding="utf-8", newline="").write(rt)
        print("README-投稿包 已同步")
    else:
        print("README-投稿包 无需修改")
PYEOF_MARK = None
