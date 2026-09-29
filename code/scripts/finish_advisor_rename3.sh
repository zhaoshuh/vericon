#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
# -*- coding: utf-8 -*-
AP = "/mnt/f/文献/AgentOps"

def edit(path, pairs):
    t = open(path, encoding="utf-8").read()
    hits = []
    for o, n in pairs:
        c = t.count(o)
        hits.append(c)
        t = t.replace(o, n)
    open(path, "w", encoding="utf-8", newline="").write(t)
    print(f"  {path.split('AgentOps/')[-1]}: counts={hits}")

print("[1] 01-进度.md（仅审计相关行）:")
edit(f"{AP}/01-进度.md", [
    ("**导师复核第二批 20 条（独立种子）：20✅ + 0⚠️ + 0❌（100%）**；合并 40 条 **0 错误**（合并严格 90%）；详见 `实验记录/G1-约束抽检-第一批.md`（含导师复核节）与 `导师复核意见-2026-09-27.md`；待真实导师最终确认",
     "**独立复核第二批 20 条（独立种子）：20✅ + 0⚠️ + 0❌（100%）**；合并 40 条 **0 错误**（合并严格 90%）；详见 `实验记录/G1-约束抽检-第一批.md`（含独立复核节）与 `独立复核意见-2026-09-27.md`；待人类签核（可选）"),
    ("→ 待导师 5 分钟签字", "→ 待真人签核（5 分钟；可选）"),
    ("| 2026-09-27 | 导师复核 | **G1 独立复核通过**：导师角色独立第二批抽样（seed 20260927）20 条全对；两批 40 条 **0 错误**；审计注记回填（C004 补证 compilation.py:1138 等 7 条）；产出 `导师复核意见-2026-09-27.md`（4 项整改清单） |",
     "| 2026-09-27 | 独立复核 | **G1 独立复核通过**：独立复核角色（AI 实例）第二批抽样（seed 20260927）20 条全对；两批 40 条 **0 错误**；审计注记回填（C004 补证 compilation.py:1138 等 7 条）；产出 `独立复核意见-2026-09-27.md`（4 项整改清单） |"),
])

print("[2] Paper1-冲A改造方案.md:")
edit(f"{AP}/论文/Paper1-冲A改造方案.md", [
    ("基于 Paper1-draft-v2 现状与导师复核意见（A2/A4 项）", "基于 Paper1-draft-v2 现状与独立复核意见（A2/A4 项）"),
])

print("[3] 独立审查-AI角色-2026-09-28.md:")
edit(f"{AP}/实验记录/独立审查-AI角色-2026-09-28.md", [
    ("导师/合作者按第四节逐项浏览", "同事/合作者按第四节逐项浏览"),
])

# 验证
print("\n[验证] 三文件中残留 '导师':")
for f in [f"{AP}/01-进度.md", f"{AP}/论文/Paper1-冲A改造方案.md", f"{AP}/实验记录/独立审查-AI角色-2026-09-28.md"]:
    t = open(f, encoding="utf-8").read()
    import re
    occ = [m.start() for m in re.finditer('导师', t)]
    ctx = [t[max(0, i-25):i+25].replace('\n', ' ') for i in occ[:5]]
    print(f"  {f.split('AgentOps/')[-1]}: {len(occ)} 处")
    for c in ctx:
        print("     …", c, "…")
PYEOF
