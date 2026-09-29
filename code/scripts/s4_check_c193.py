#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C193 专用验证：PoolerConfig 对已移除键 'normalize' 的拒绝行为（removed-key 检查属特例，绕过未知键保护）"""
import json
import os
from datetime import datetime, timezone

os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from vllm.config import PoolerConfig  # noqa: E402

OUT = "/mnt/f/文献/AgentOps/实验记录/S4验证/records_model2.jsonl"

rec = {
    "constraint_id": "C193", "track": "A", "engine": "vllm-0.30.0",
    "expr": "PoolerConfig 不再接受字段 'normalize'：传入即报错，应改用 use_activation",
    "config": {"normalize": True}, "violates": "removed key 'normalize' accepted",
    "run_at": datetime.now(timezone.utc).isoformat(),
    "strategy": "S1:PoolerConfig(manual-removed-key)",
}

# 基线
try:
    PoolerConfig()
    base_ok = True
except Exception as e:
    base_ok = False
    print("baseline FAIL:", type(e).__name__, str(e)[:200])

# 违反：传入已移除键
try:
    PoolerConfig(normalize=True)
    rec.update({"status": "no_error", "observed": "constructed_ok（normalize 被接受）"})
except Exception as e:
    rec.update({"status": "confirmed", "observed": f"{type(e).__name__}: {str(e)[:300]}"})

with open(OUT, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("baseline_ok:", base_ok)
print("C193:", rec["status"], "|", rec.get("observed", "")[:160])
