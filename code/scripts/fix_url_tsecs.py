# -*- coding: utf-8 -*-
"""修正为直连入口 tse-cs，并加"错误站点"警告"""
LAT = "/mnt/f/文献/AgentOps/论文/latex"
p = f"{LAT}/投稿-提交清单.md"
t = open(p, encoding="utf-8").read()

old_block_start = "1. 打开 **IEEE Computer Society 投稿入口**"
i = t.find(old_block_start)
if i >= 0:
    j = t.find("\n\n", i)
    new = ("1. 打开 **直连入口（已核实）**：`https://mc.manuscriptcentral.com/tse-cs`\n"
           "   - 站点配置原文：`account: { id:\"Transactions on Software Engineering\", publisher_name:\"IEEE\", short_name:\"tse-cs\" }`\n"
           "   - 备选路径：`https://mc.manuscriptcentral.com/cs-ieee` → Journal 下拉选 **Transactions on Software Engineering** → Log In\n"
           "   ⚠️ **绝对不要用 `mc.manuscriptcentral.com/tse`**：那是 **Oxford University Press 的《Transportation Safety and Environment》**"
           "（缩写同为 TSE，站点配置 `publisher_name:\"Oxford University Press\"`）——投错期刊！若已在那边建了草稿，**不要提交**，删除即可（未提交不构成重复投稿）。")
    t = t[:i] + new + t[j:]
else:
    t = t.replace("https://mc.manuscriptcentral.com/cs-ieee", "https://mc.manuscriptcentral.com/tse-cs")
open(p, "w", encoding="utf-8", newline="").write(t)
print("清单已改为 tse-cs 直连 + 错误站点警告")

r = f"{LAT}/README-投稿包.md"
rt = open(r, encoding="utf-8").read()
rt = rt.replace("https://mc.manuscriptcentral.com/cs-ieee（Journal 下拉选 Transactions on Software Engineering）",
                "https://mc.manuscriptcentral.com/tse-cs（直连；切勿用 mc.manuscriptcentral.com/tse —— 那是 Transportation Safety and Environment）")
open(r, "w", encoding="utf-8", newline="").write(rt)
print("README 已同步")
