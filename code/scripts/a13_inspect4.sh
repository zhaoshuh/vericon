#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "===== 参数清单.json 结构 ====="
$PY - <<'PYEOF'
import json
d = json.load(open('/mnt/f/文献/AgentOps/实验记录/参数清单.json', encoding='utf-8'))
print("keys:", list(d.keys())[:15])
print("meta:", json.dumps(d.get('meta', {}), ensure_ascii=False)[:400])
for k, v in d.items():
    if isinstance(v, list):
        print(f"list '{k}': len={len(v)}")
        if v and isinstance(v[0], dict):
            print("  item keys:", list(v[0].keys()))
            break
    elif isinstance(v, dict):
        print(f"dict '{k}':", list(v.keys())[:15])
PYEOF
echo ""
echo "===== P2 目录 + 脚本 ====="
ls '/mnt/f/文献/AgentOps/实验记录/P2-版本研究/' | head -15
ls /mnt/f/文献/AgentOps/代码/scripts/ | grep -i 'ver\|scan\|flag\|param' | head -15
echo ""
echo "===== 全仓搜 '165'（论文与实验记录） ====="
grep -rn '165\.4\|165\.39' '/mnt/f/文献/AgentOps/论文/' /mnt/f/文献/AgentOps/实验记录/*.md 2>/dev/null | head -10
echo ""
echo "===== SGLang snapshot 内的版本线索 ====="
ls '/mnt/f/文献/AgentOps/代码/third_party/sglang-v0.5.20/' | head -20
cat '/mnt/f/文献/AgentOps/代码/third_party/sglang-v0.5.20/python/sglang/version.py' 2>/dev/null
find '/mnt/f/文献/AgentOps/代码/third_party/sglang-v0.5.20' -maxdepth 2 -name '*.txt' -o -maxdepth 2 -name 'VERSION' -o -maxdepth 2 -name '*.json' 2>/dev/null | head -8
