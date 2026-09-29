#!/usr/bin/env bash
PY=~/.venvs/agentops-py311/bin/python
C1='/mnt/f/文献/AgentOps/实验记录/C1-人类盲标'
echo "=== CSV 结构自检 ==="
$PY - <<PYEOF
import csv
rows = list(csv.DictReader(open("$C1/标注表-可填.csv", encoding="utf-8-sig")))
print("rows:", len(rows), "| cols:", list(rows[0].keys()))
print("示例 id:", rows[0]["id"], "| file:", rows[0]["file"], "| 上下文行数:", rows[0]["context"].count(chr(10))+1)
PYEOF
echo ""
echo "=== 端到端小测：模拟“人类填中文”后导入 ==="
$PY - <<PYEOF
import csv
src = "$C1/标注表-可填.csv"
out = "$C1/_test_human.csv"
rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
vals = ["是", "否", "不确定"]
for i, r in enumerate(rows):
    r["verdict"] = vals[i % 2]  # 交替填 是/否
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print("模拟填写完成（是/否 交替）")
PYEOF
cp "$C1/_test_human.csv" "$C1/c1_results.csv"
$PY /mnt/f/文献/AgentOps/代码/scripts/c1_import_results.py 2>&1 | tail -12
echo ""
echo "=== 清理测试文件（保留下载用的真实模板） ==="
rm -f "$C1/_test_human.csv" "$C1/C1-导入结果.json"
ls -la "$C1" | grep -E 'csv|html|md'
