#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
$PY - <<'PYEOF'
import json
for f in ['/mnt/f/文献/AgentOps/实验记录/P1b-金标准样本.json',
          '/mnt/f/文献/AgentOps/实验记录/P1b-金标准样本2.json',
          '/mnt/f/文献/AgentOps/实验记录/P1b-标注结果.json']:
    try:
        d = json.load(open(f, encoding='utf-8'))
        print("=====", f)
        if isinstance(d, dict):
            print("keys:", list(d.keys())[:12])
            for k, v in d.items():
                if isinstance(v, list):
                    print(f"list '{k}': len={len(v)}; item0 keys={list(v[0].keys()) if v and isinstance(v[0], dict) else v[:2]}")
                    if v and isinstance(v[0], dict):
                        print("  item0:", json.dumps(v[0], ensure_ascii=False)[:300])
                    break
        else:
            print("list len:", len(d), "item0:", json.dumps(d[0], ensure_ascii=False)[:300] if d else None)
    except Exception as e:
        print("=====", f, "ERR", e)
PYEOF
