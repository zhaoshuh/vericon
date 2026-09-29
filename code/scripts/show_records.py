"""查看统一实验记录（纯标准库，Windows/WSL 均可跑）。

用法：
    python scripts/show_records.py                 # 最近 20 条
    python scripts/show_records.py --ok-only -n 50 # 只看成功记录
    python scripts/show_records.py --backend vidur_sim
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentops.record import read_records  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("-n", "--limit", type=int, default=20)
    p.add_argument("--ok-only", action="store_true")
    p.add_argument("--backend", default=None)
    args = p.parse_args()

    records = read_records()
    if args.backend:
        records = [r for r in records if r.get("backend") == args.backend]
    if args.ok_only:
        records = [r for r in records if r.get("status") == "ok"]
    records = records[-args.limit:]

    header = (f"{'run_id':<34} {'status':<6} {'seqs':>5} {'batched':>8} "
              f"{'ttft_p90':>9} {'tpot_p90':>9} {'goodput':>8} {'wall_s':>8} {'gpu_h':>6}")
    print(header)
    print("-" * len(header))
    for r in records:
        cfg, met, cost = r.get("config", {}), r.get("metrics", {}), r.get("cost", {})

        def fmt(v, w=0):
            return "-" if v is None else (f"{v:.{w}f}" if isinstance(v, float) else str(v))

        print(f"{r.get('run_id', '?'):<34} {r.get('status', '?'):<6} "
              f"{fmt(cfg.get('max_num_seqs')):>5} {fmt(cfg.get('max_num_batched_tokens')):>8} "
              f"{fmt(met.get('ttft_p90_s'), 4):>9} {fmt(met.get('tpot_p90_s'), 4):>9} "
              f"{fmt(met.get('goodput_rps'), 3):>8} {fmt(cost.get('wall_clock_s'), 1):>8} "
              f"{fmt(cost.get('gpu_hours'), 3):>6}")
    if not records:
        print("（没有记录。先跑 `bash scripts/run_one.sh ...`）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
