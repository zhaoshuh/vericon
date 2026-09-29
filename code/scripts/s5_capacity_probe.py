# -*- coding: utf-8 -*-
"""S5 容量标定：找 Llama-2-7b/A100/TP1 在 splitwise_conv 负载下的容量点，确定扫参 qps。"""
import sys
sys.path.insert(0, "/mnt/f/文献/AgentOps/代码")

from agentops.backends.vidur_backend import VidurRunSpec, run  # noqa: E402

print(f"{'qps':>5} {'status':>7} {'thr':>7} {'ttft90':>8} {'tpot90':>8} {'goodput':>8} {'slo_ok':>7}")
for qps in [8.0, 12.0, 16.0, 24.0, 32.0, 48.0, 64.0]:
    spec = VidurRunSpec(
        max_num_seqs=128,
        max_num_batched_tokens=4096,
        block_size=16,
        watermark_blocks_fraction=0.01,
        qps=qps,
        num_requests=256,
        length_trace="splitwise_conv.csv",
    )
    rec = run(spec, study="s5-probe", trial=int(qps))
    m = rec.metrics or {}
    print(f"{qps:>5} {rec.status:>7} "
          f"{m.get('throughput_rps', 0):>7.3f} {m.get('ttft_p90_s', 0):>8.3f} {m.get('tpot_p90_s', 0):>8.4f} "
          f"{m.get('goodput_rps', 0):>8.3f} {str(m.get('slo_ok')):>7}")
    if rec.status != "ok":
        print("   err:", (rec.error or "")[:180])
