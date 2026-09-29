# -*- coding: utf-8 -*-
"""① 生成零脚本 CSV 可填表（Excel 打开即可）② 硬化 HTML（脚本被禁时给出提示）③ 更新非专业者说明"""
import csv
import json
import os

C1 = "/mnt/f/文献/AgentOps/实验记录/C1-人类盲标"
pack = json.load(open(f"{C1}/sites-pack.json", encoding="utf-8"))["items"]

# ---------- ① CSV ----------
out = f"{C1}/标注表-可填.csv"
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "verdict", "note", "file", "line", "tier", "kind", "condition", "message", "context"])
    for it in pack:
        ctx = "\n".join(f"{ln}: {tx}" for ln, tx in it["context"])
        w.writerow([it["id"], "", "", it["file"], it["line"], it.get("tier", ""), it.get("kind", ""),
                    (it.get("condition") or "")[:400], (it.get("message") or "")[:300], ctx])
print("CSV ->", out, len(pack), "rows")

# ---------- ② 硬化 HTML ----------
h = f"{C1}/标注工具.html"
t = open(h, encoding="utf-8").read()
reps = [
    ("let state = JSON.parse(localStorage.getItem(KEY) || '{}');",
     "let state = {};\ntry { state = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { state = {}; }"),
    ("function save(){ localStorage.setItem(KEY, JSON.stringify(state)); }",
     "function save(){ try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }"),
    ("render();\n</script>",
     ("try { render(); } catch (err) {\n"
      "  document.getElementById('list').innerHTML = '<div class=\"card\"><b>渲染失败（可能是浏览器/查看器禁用了脚本）</b><br>' + err + "
      "'<br><br>请改用同目录的 <b>标注表-可填.csv</b>：用 Excel 打开，在 <b>verdict</b> 列逐行填 Y / N / U（或 是 / 否 / 不确定），保存后发回即可。</div>';\n"
      "}\n</script>")),
]
for i, (o, n) in enumerate(reps, 1):
    c = t.count(o)
    print(f"HTML patch{i}: count={c}")
    if c == 1:
        t = t.replace(o, n)
open(h, "w", encoding="utf-8", newline="").write(t)

# ---------- ③ 更新说明 ----------
m = f"{C1}/标注说明-给非专业者.md"
t = open(m, encoding="utf-8").read()
add = """

---

## 6. 如果 HTML 里看不到题目（只显示了这段说明）

某些查看器/受限环境**不执行网页脚本**，这时题目列表出不来。两个办法：

**办法 A（推荐，零依赖）**：用 Excel（或 WPS）打开同目录的 **`标注表-可填.csv`**：
- 每行一个站点；`context` 列是源码上下文；
- 只需在 **`verdict`** 列填 **Y / N / U**（或写 **是 / 否 / 不确定**），`note` 列可选；
- 保存后把文件发回即可（其余列不要改动）。

**办法 B**：把 `标注工具.html` 用 **Chrome / Edge 双击打开**（不要用网页预览器），即可看到题目卡片。
"""
if "如果 HTML 里看不到题目" not in t:
    open(m, "w", encoding="utf-8", newline="").write(t + add)
    print("说明已更新")
else:
    print("说明已含该节")
PYEOF_MARK = None
