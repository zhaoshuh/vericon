"""跑通"一条配置"的最小闭环：配置 → 指标 → 成本 → 统一记录。

示例（WSL，本机）：
    python -m agentops.run_one --max-num-seqs 64 --max-num-batched-tokens 2048
示例（GPU 机器）：
    python -m agentops.run_one --backend vllm --max-num-seqs 64 --max-num-batched-tokens 2048
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .paths import records_dir
from .record import append_record, summarize


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="跑一条配置并写入统一实验记录")
    p.add_argument("--backend", choices=["vidur", "vllm"], default="vidur")
    # 被调参数
    p.add_argument("--max-num-seqs", type=int, default=64)
    p.add_argument("--max-num-batched-tokens", type=int, default=2048)
    # 工作负载 / 硬件
    p.add_argument("--device", default="a100", help="vidur: a40|a100|h100")
    p.add_argument("--model", default=None, help="默认：vidur 用 Llama-2-7b-hf，vllm 用 Qwen2.5-1.5B-Instruct")
    p.add_argument("--tp", type=int, default=1, help="tensor parallel size")
    p.add_argument("--pp", type=int, default=1, help="pipeline parallel stages（仅 vidur）")
    p.add_argument("--qps", type=float, default=8.0, help="请求到达率（仅 vidur）")
    p.add_argument("--num-requests", type=int, default=256)
    p.add_argument("--length-trace", default="splitwise_conv.csv", help="仅 vidur：data/processed_traces 下的文件")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--slo-ttft-p90-s", type=float, default=2.0)
    p.add_argument("--slo-tpot-p90-s", type=float, default=0.2)
    # vllm 专用
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--max-tokens", type=int, default=128, help="每请求生成上限（仅 vllm）")
    # 记录
    p.add_argument("--study-name", default=None)
    p.add_argument("--trial", type=int, default=None)
    p.add_argument("--print-json", action="store_true")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.backend == "vidur":
        from .backends.vidur_backend import VidurRunSpec, run as vidur_run

        spec = VidurRunSpec(
            max_num_seqs=args.max_num_seqs,
            max_num_batched_tokens=args.max_num_batched_tokens,
            device=args.device,
            model=args.model or "meta-llama/Llama-2-7b-hf",
            tp=args.tp, pp=args.pp,
            qps=args.qps,
            num_requests=args.num_requests,
            length_trace=args.length_trace,
            seed=args.seed,
            slo_ttft_p90_s=args.slo_ttft_p90_s,
            slo_tpot_p90_s=args.slo_tpot_p90_s,
        )
        record = vidur_run(spec, study=args.study_name, trial=args.trial)
    else:
        from .backends.vllm_backend import VllmRunSpec, run as vllm_run

        spec = VllmRunSpec(
            max_num_seqs=args.max_num_seqs,
            max_num_batched_tokens=args.max_num_batched_tokens,
            model=args.model or "Qwen/Qwen2.5-1.5B-Instruct",
            port=args.port,
            num_requests=args.num_requests,
            concurrency=args.concurrency,
            max_tokens=args.max_tokens,
            tensor_parallel_size=args.tp,
            slo_ttft_p90_s=args.slo_ttft_p90_s,
            slo_tpot_p90_s=args.slo_tpot_p90_s,
        )
        record = vllm_run(spec, study=args.study_name, trial=args.trial)

    paths = append_record(record, records_dir())
    print(summarize(record.to_dict()))
    print(f"记录已写入: {paths['jsonl']}")
    if args.print_json:
        print(json.dumps(record.to_dict(), ensure_ascii=False, indent=2))
    return 0 if record.status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
