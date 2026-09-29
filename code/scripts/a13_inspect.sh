#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "===== 1) SGLang 图文件与 meta ====="
ls -la /mnt/f/文献/AgentOps/实验记录/P3-sglang/ | head -20
echo "--- sglang-v0.5.20-params.json 前 40 行 ---"
head -40 '/mnt/f/文献/AgentOps/实验记录/P3-sglang/sglang-v0.5.20-params.json'
echo "--- 本地仓库 commit ---"
cd /mnt/f/文献/AgentOps/代码/third_party/sglang-v0.5.20 2>/dev/null && git rev-parse HEAD 2>/dev/null && git describe --tags 2>/dev/null | head -2
echo ""
echo "===== 2) 约束图-v1-ext 结构 ====="
$PY - <<'PYEOF'
import json
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/约束图-v1-ext.json', encoding='utf-8'))
print("top keys:", list(d.keys())[:20])
for k, v in d.items():
    if isinstance(v, list):
        print(f"list key '{k}': len={len(v)}")
        if v and isinstance(v[0], dict):
            print("  first item keys:", list(v[0].keys())[:14])
            ev = [x for x in v if x.get('evidence') or x.get('source') or x.get('file')]
            print("  with evidence-ish field:", len(ev), "/", len(v))
            break
PYEOF
echo ""
echo "===== 3) 版本对比.md 表头与 262 ====="
sed -n '1,30p' '/mnt/f/文献/AgentOps/实验记录/P2-版本研究/版本对比.md'
echo "--- 262 出现处 ---"
grep -n '262' '/mnt/f/文献/AgentOps/实验记录/P2-版本研究/版本对比.md' | head
echo ""
echo "===== 4) S6 原始数据 ====="
ls /mnt/f/文献/AgentOps/实验记录/ | grep -i 'S6\|anchor\|llama' | head
find /mnt/f/文献/AgentOps/实验记录 -iname '*anchor*' -o -iname '*llamacpp*.csv' 2>/dev/null | head -8
echo "--- S6 报告 line 40-60 ---"
sed -n '40,60p' '/mnt/f/文献/AgentOps/实验记录/S6-真机锚点-报告.md'
