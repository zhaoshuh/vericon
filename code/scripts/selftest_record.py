"""统一记录格式的离线自检（不需要 vidur/vllm，纯标准库）。

用法（Windows 或 WSL 均可）：
    python scripts/selftest_record.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentops.record import (  # noqa: E402
    RunRecord, append_record, flatten, new_run_id, read_records, summarize,
)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        rec = RunRecord(
            run_id=new_run_id("selftest"),
            backend="vidur_sim",
            mode="simulate",
            study="selfcheck",
            trial=0,
            config={
                "max_num_seqs": 64,
                "max_num_batched_tokens": 2048,
                "constraints_applied": ["max_num_batched_tokens >= max_num_seqs"],
                "nested": {"a": 1},
            },
            metrics={"ttft_p90_s": 0.5, "tpot_p90_s": 0.05, "goodput_rps": 7.1, "slo_ok": True},
            cost={"wall_clock_s": 12.3, "gpu_hours": 0.0, "gpu_hours_if_real": 0.02, "llm_tokens": 0},
            environment={"python": "3.14", "backend": "vidur"},
            artifacts={"output_dir": str(tmp_dir)},
        )
        paths = append_record(rec, tmp_dir)

        # 再追加一条"失败"记录，验证表头扩展与失败落盘
        rec2 = RunRecord(run_id=new_run_id("selftest"), status="failed",
                         error="RuntimeError: boom",
                         config={"max_num_seqs": 999999, "max_num_batched_tokens": 1})
        append_record(rec2, tmp_dir)

        records = read_records(tmp_dir)
        flat = flatten(rec.to_dict())
        csv_text = paths["csv"].read_text(encoding="utf-8-sig")
        header = csv_text.splitlines()[0]

        checks = {
            "JSONL 写入 2 条": len(records) == 2,
            "失败记录也落盘": records[1]["status"] == "failed",
            "嵌套字段被扁平化": flat["config.nested.a"] == 1,
            "列表被 JSON 序列化": json.loads(flat["config.constraints_applied"])[0].startswith("max_num"),
            "CSV 含新字段(扩展表头)": "error" in header and "metrics.goodput_rps" in header,
            "CSV 行数与 JSONL 一致": len(csv_text.strip().splitlines()) == 3,
            "成本字段存在": flat["cost.gpu_hours"] == 0.0 and flat["cost.wall_clock_s"] == 12.3,
        }
        for name, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'}  {name}")
        print("示例摘要:", summarize(rec.to_dict()))
        return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
