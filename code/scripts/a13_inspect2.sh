#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
echo "===== main.tex: 259/262/165/159 ====="
grep -n '259\|262\|165\.4\|159\.77' '/mnt/f/文献/AgentOps/论文/latex/main.tex' | head -15
echo ""
echo "===== SGLang 420 约束产物在哪 ====="
find /mnt/f/文献/AgentOps/实验记录 -iname '*sglang*' -o -iname '*SGLang*' 2>/dev/null | grep -v third_party | head -20
echo ""
echo "===== candidates meta ====="
$PY - <<'PYEOF'
import json
for f in ['/mnt/f/文献/AgentOps/实验记录/P3-sglang/sglang-v0.5.20-candidates.json']:
    d = json.load(open(f, encoding='utf-8'))
    print(f, "-> keys:", list(d.keys())[:10])
    print("  meta:", json.dumps(d.get('meta', {}), ensure_ascii=False)[:300])
    for k, v in d.items():
        if isinstance(v, list):
            print(f"  list '{k}': len={len(v)}")
PYEOF
echo ""
echo "===== S6 5rep CSV 分析 ====="
head -3 '/mnt/f/文献/AgentOps/实验记录/llamacpp_anchor_5rep.csv'
$PY - <<'PYEOF'
import csv
for f in ['/mnt/f/文献/AgentOps/实验记录/llamacpp_anchor_5rep.csv', '/mnt/f/文献/AgentOps/实验记录/llamacpp_anchor.csv']:
    rows = list(csv.DictReader(open(f, encoding='utf-8-sig')))
    print(f"--- {f} n={len(rows)}")
    if not rows: continue
    print("   cols:", list(rows[0].keys())[:14])
    # 找 pp 列
    ppk = [k for k in rows[0] if 'pp' in k.lower() and 'ts' in k.lower() or 'pp512' in k.lower()]
    tgk = [k for k in rows[0] if 'tg' in k.lower()]
    pk = ppk[0] if ppk else None
    tk = tgk[0] if tgk else None
    print("   pp col:", pk, "tg col:", tk)
    if pk:
        best = max(rows, key=lambda r: float(r[pk] or 0))
        print("   best pp512:", {k: best[k] for k in list(best.keys())[:8]}, "=>", best[pk])
    if tk:
        best2 = max(rows, key=lambda r: float(r[tk] or 0))
        print("   best tg64 :", {k: best2[k] for k in list(best2.keys())[:8]}, "=>", best2[tk])
PYEOF
