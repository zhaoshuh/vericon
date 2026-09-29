#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "===== cli_flags 对比：参数清单.json vs P2/v0.30.0-params.json ====="
$PY - <<'PYEOF'
import json

d1 = json.load(open('/mnt/f/文献/AgentOps/实验记录/参数清单.json', encoding='utf-8'))
d2 = json.load(open('/mnt/f/文献/AgentOps/实验记录/P2-版本研究/v0.30.0-params.json', encoding='utf-8'))

print("参数清单 counts:", d1['counts'])
f1 = d1.get('cli_flags', [])
print("参数清单 cli_flags len:", len(f1), "| item0:", json.dumps(f1[0], ensure_ascii=False)[:200] if f1 else None)

print("P2 counts:", d2.get('counts'))
f2 = d2.get('cli_flags', [])
print("P2 cli_flags len:", len(f2), "| item0:", json.dumps(f2[0], ensure_ascii=False)[:200] if f2 else None)

def names(lst):
    out = []
    for x in lst:
        if isinstance(x, dict):
            out.append(x.get('name') or x.get('flag') or x.get('option') or '')
        else:
            out.append(str(x))
    return out

n1, n2 = set(names(f1)), set(names(f2))
print("distinct names: 参数清单", len(n1), "| P2", len(n2))
print("only-in-清单:", sorted(n1 - n2)[:10])
print("only-in-P2:", sorted(n2 - n1)[:10])
# 列名类型分布
if f1 and isinstance(f1[0], dict):
    print("清单 item keys:", list(f1[0].keys()))
if f2 and isinstance(f2[0], dict):
    print("P2 item keys:", list(f2[0].keys()))
PYEOF
echo ""
echo "===== sglang 下载来源线索 ====="
grep -rn 'sglang.*tar\|sglang.*zip\|github.*sglang\|sglang.*download' /mnt/f/文献/AgentOps/代码/scripts/*.sh /mnt/f/文献/AgentOps/代码/scripts/*.py 2>/dev/null | head -6
