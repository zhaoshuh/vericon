# -*- coding: utf-8 -*-
"""最终修正投稿入口：IEEE Author Portal（Atypon）+ 记录 tse-cs ScholarOne 只收邀请稿"""
import os
LAT = "/mnt/f/文献/AgentOps/论文/latex"

portal = "https://ieee.atyponrex.com/journal/tse-cs"
note = f"""TSE 投稿入口（2026-09-29 实测确认）
=====================================

**正确入口 = IEEE Author Portal（Atypon ReX）**：
    {portal}
（该页会跳转 IEEE 账号登录；也可从 IEEE TSE 的 ScholarOne 作者面板上的
  "IEEE Transactions on Software Engineering Author Portal" 链接进入。）

⚠️ 三条容易踩的坑（都实测过）：
1. `mc.manuscriptcentral.com/tse` = **Oxford University Press《Transportation Safety and Environment》**（缩写同为 TSE）——投错期刊！
2. `mc.manuscriptcentral.com/tse-cs` = IEEE TSE 的 ScholarOne，但页面明示：
   "**This site is no longer used for new submissions**, please visit the IEEE Transactions on Software Engineering Author Portal…
    This site only accepts invited submissions." → 只收邀请稿，**新投稿必须走 Author Portal**。
3. `authorportal.ieee.org` 在本机网络下不可达（ERR_TUNNEL_CONNECTION_FAILED）；自动化浏览器访问 IEEE 账号页会被拒
   （"The requested URL was rejected"）→ **投稿需在你的浏览器里人工完成**，我提供全程指引与现成字段。

投稿件：
- 稿件 PDF：`F:\\文献\\AgentOps\\论文\\latex\\main-final.pdf`（11 页、199 词摘要）
- 封面信 PDF：`F:\\文献\\AgentOps\\论文\\latex\\cover-letter.pdf`
- 字段清单（标题/摘要/关键词/作者/审稿人/声明）：`F:\\文献\\AgentOps\\论文\\latex\\投稿-提交清单.md`
"""
open(f"{LAT}/投稿入口-最终说明.txt", "w", encoding="utf-8", newline="").write(note)

p = f"{LAT}/投稿-提交清单.md"
t = open(p, encoding="utf-8").read()
old_start = "1. 打开 **直连入口（已核实）**"
i = t.find(old_start)
if i >= 0:
    j = t.find("\n\n", i)
    new = (f"1. **正确入口 = IEEE Author Portal**：`{portal}`\n"
           "   - 该页会跳转 IEEE 账号登录（需 IEEE 账号；建议绑定 ORCID）\n"
           "   - `mc.manuscriptcentral.com/tse-cs` 虽标着 IEEE TSE，但页面明示 \"**This site is no longer used for new submissions**… only accepts invited submissions\" → 新投稿必须走 Author Portal\n"
           "   ⚠️ **绝对不要用 `mc.manuscriptcentral.com/tse`**：那是 Oxford University Press 的《Transportation Safety and Environment》（缩写同为 TSE）\n"
           "   ℹ️ 本机实测：`authorportal.ieee.org` 不可达、且自动化浏览器会被 IEEE 账号页拒绝（\"The requested URL was rejected\"）→ **投稿需在你的浏览器里人工完成**；我负责给字段与逐步指引")
    t = t[:i] + new + t[j:]
open(p, "w", encoding="utf-8", newline="").write(t)
print("清单已更新为 Author Portal 入口")
