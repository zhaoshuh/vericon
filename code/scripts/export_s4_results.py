# -*- coding: utf-8 -*-
"""S4 · 导出验证结果 → 已验证约束.json / no_error / blocked，并回填 约束图.json

输入: 实验记录/约束图.json, 实验记录/S4验证/records.jsonl
输出:
  实验记录/已验证约束.json            （confirmed，进入论文 artifact；硬约束要求）
  实验记录/S4验证/no_error.json       （基线可构造但违反未在构造期报错）
  实验记录/S4验证/blocked.json        （无法在构造期构造：运行期/依赖限制）
  实验记录/约束图.json                （回填 validation 字段；保留 v1 快照不动）
用法: python export_s4_results.py
"""
import json
import os
from datetime import datetime, timezone

ROOT = r"F:\文献\AgentOps\实验记录"
GRAPH = os.path.join(ROOT, "约束图.json")
REC = os.path.join(ROOT, "S4验证", "records.jsonl")
OUT_OK = os.path.join(ROOT, "已验证约束.json")
OUT_NE = os.path.join(ROOT, "S4验证", "no_error.json")
OUT_BL = os.path.join(ROOT, "S4验证", "blocked.json")


def main():
    graph = json.load(open(GRAPH, encoding="utf-8"))
    records = {}
    with open(REC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                records[r["constraint_id"]] = r  # 后写覆盖（最新一轮为准）

    confirmed, no_error, blocked = [], [], []
    for node in graph["nodes"]:
        cid = node["id"]
        r = records.get(cid)
        if not r:
            node["validation"] = {"status": "not_tested", "track": "A", "note": "S4 用例未覆盖（构造期不可构造或未收集）"}
            continue
        node["validation"] = {
            "status": r["status"],
            "track": r.get("track", "A"),
            "engine": r.get("engine"),
            "strategy": r.get("strategy"),
            "observed": (r.get("observed") or r.get("detail") or "")[:500],
            "run_at": r.get("run_at"),
            "source": "S4-trackA（vLLM 配置构造校验路径）",
        }
        if r["status"] == "confirmed":
            confirmed.append(node)
        elif r["status"] == "no_error":
            no_error.append(node)
        else:
            blocked.append(node)

    now = datetime.now(timezone.utc).isoformat()
    graph["meta"]["validated_at"] = now

    ok_doc = {
        "meta": {
            "engine": "vllm-0.30.0",
            "commit": graph["meta"].get("commit"),
            "exported_at": now,
            "method": "S4 轨道A：构造违反配置 → 经 vLLM 真实配置校验路径（pydantic/dataclass 构造）→ 期望报错",
            "note": "confirmed = 违反赋值确实被引擎拒绝；no_error = 基线可构造但违反未在构造期暴露；blocked = 运行期/依赖限制无法构造。",
        },
        "stats": {
            "confirmed": len(confirmed),
            "no_error": len(no_error),
            "blocked": len(blocked),
            "graph_total": len(graph["nodes"]),
            "confirmed_ratio_all": round(len(confirmed) / max(1, len(graph["nodes"])), 3),
        },
        "constraints": confirmed,
    }
    with open(OUT_OK, "w", encoding="utf-8") as f:
        json.dump(ok_doc, f, ensure_ascii=False, indent=2)
    with open(OUT_NE, "w", encoding="utf-8") as f:
        json.dump({"stats": {"no_error": len(no_error)}, "constraints": no_error}, f, ensure_ascii=False, indent=2)
    with open(OUT_BL, "w", encoding="utf-8") as f:
        json.dump({"stats": {"blocked": len(blocked)}, "constraints": blocked}, f, ensure_ascii=False, indent=2)
    with open(GRAPH, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(json.dumps(ok_doc["stats"], ensure_ascii=False))
    print("->", OUT_OK)
    print("->", OUT_NE)
    print("->", OUT_BL)
    print("->", GRAPH, "(validation 回填)")


if __name__ == "__main__":
    main()
