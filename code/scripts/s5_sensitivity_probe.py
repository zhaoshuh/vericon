# -*- coding: utf-8 -*-
"""S5 目标敏感性探针：在 qps=12 / n=384 / 收紧 SLO 下，看不同配置的 goodput 是否拉开。"""
import sys
sys.path.insert(0, "/mnt/f/文献/AgentOps/代码")

from agentops.backends.vidur_backend import VidurRunSpec, run  # noqa: E402

CONFIGS = [
    dict(max_num_seqs=64, max_num_batched_tokens=2048, watermark_blocks_fraction=0.01),
    dict(max_num_seqs=256, max_num_batched_tokens=8192, watermark_blocks_fraction=0.01),
    dict(max_num_seqs=256, max_num_batched_tokens=2048, watermark_blocks_fraction=0.10),
    dict(max_num_seqs=32, max_num_batched_tokens=1024, watermark_blocks_fraction=0.05),
    dict(max_num_seqs=128, max_num_batched_tokens=4096, watermark_blocks_fraction=0.01),
]

print(f"{'mns':>4} {'mtib':>5} {'wm':>5} | {'status':>6} {'thr':>7} {'ttft90':>8} {'tpot90':>8} {'goodput':>8} {'slo_ok':>6} {'met':>4}")
for c in CONFIGS:
    spec = VidurRunSpec(
        **c,
        block_size=16,
        qps=12.0,
        num_requests=384,
        length_trace="splitwise_conv.csv",
        slo_ttft_p90_s=1.0,
        slo_tpot_p90_s=0.1,
    )
    rec = run(spec, study="s5-sens", trial=c["max_num_seqs"])
    m = rec.metrics or {}
    print(f"{c['max_num_seqs']:>4} {c['max_num_batched_tokens']:>5} {c['watermark_blocks_fraction']:>5} | "
          f"{rec.status:>6} {m.get('throughput_rps', 0):>7.3f} {m.get('ttft_p90_s', 0):>8.3f} {m.get('tpot_p90_s', 0):>8.4f} "
          f"{m.get('goodput_rps', 0):>8.3f} {str(m.get('slo_ok')):>6} {m.get('slo_met_requests', 0):>4}")
    if rec.status != "ok":
        print("   err:", (rec.error or "")[:200])
