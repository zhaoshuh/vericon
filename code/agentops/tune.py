"""Optuna 调优（S2: 2 维；S5: 4 维 + 三臂对照 N/M/A）。

臂定义（S5-实验设计-v1.md）：
    N  无约束 BO      —— mtib 自由采样（可违反 mtib>=mns / mtib>=负载 prefill）
    M  人工约束 BO    —— SCOOT 式人工约束：mtib >= max(mns, tokens_min)
    A  自动约束 BO    —— 我们的约束图投影：同 M（当前 Vidur 子空间下两臂等价；
                          真实 vLLM 侧差异见 已验证约束.json 的 111 条）

维度（--space-mode 5d）：
    max_num_seqs            ∈ [seq-min, seq-max]（log）
    max_num_batched_tokens  ∈ [mns|seq-min, tokens-max]（log，受臂约束）
    block_size              ∈ {8,16,32}
    watermark_blocks_fraction ∈ [wm-min, wm-max]（log；已验证约束 watermark<1）
    （num_blocks 保持自动，不采样）

目标函数：最大化 goodput_rps（满足逐请求 SLO 的请求数/秒）。
成本模型：合法试验 = 1 单位；非法/失败 = 1 + c_invalid（默认 3.0）。
所有 trial 写入统一实验记录（配置→指标→成本），失败也记录。

示例：
    python -m agentops.tune --n-trials 20 --study-name s2-smoke                  # 2 维（旧行为）
    python -m agentops.tune --space-mode 5d --arm N --seed 1 --n-trials 30 --study-name s5-N-seed1
    python -m agentops.tune --space-mode 5d --arm M --seed 1 --n-trials 30 --study-name s5-M-seed1
    python -m agentops.tune --space-mode 5d --arm A --seed 1 --n-trials 30 --study-name s5-A-seed1
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import ensure_dir, records_dir
from .record import append_record, summarize

# 搜索空间（S2 默认值；S5 用 5d 模式扩展）
DEFAULT_SPACE: Dict[str, Any] = {
    "seq_min": 16,
    "seq_max": 256,
    "tokens_max": 8192,
}


def _run_backend(args, cfg: Dict[str, Any], study_name: str, trial_number: int):
    """按 backend 分发。cfg 至少含 max_num_seqs/max_num_batched_tokens。"""
    if args.backend == "vidur":
        from .backends.vidur_backend import VidurRunSpec, run as vidur_run

        spec = VidurRunSpec(
            max_num_seqs=cfg["max_num_seqs"],
            max_num_batched_tokens=cfg["max_num_batched_tokens"],
            block_size=cfg.get("block_size", 16),
            watermark_blocks_fraction=cfg.get("watermark_blocks_fraction", 0.01),
            num_blocks=cfg.get("num_blocks"),
            max_tokens_per_request=args.max_tokens_per_request,
            device=args.device,
            model=args.model or "meta-llama/Llama-2-7b-hf",
            tp=args.tp, pp=args.pp,
            qps=args.qps,
            num_requests=args.num_requests,
            length_trace=args.length_trace,
            seed=args.seed,
            slo_ttft_p90_s=args.slo_ttft_p90_s,
            slo_tpot_p90_s=args.slo_tpot_p90_s,
            # 关键：用"搜索空间上界"（跨 trial 常量）设定预测范围 → 缓存可跨 trial 复用
            predictor_max_tokens_in_batch=args.tokens_max,
            predictor_max_batch_size=max(512, args.seq_max),
        )
        return vidur_run(spec, study=study_name, trial=trial_number)

    from .backends.vllm_backend import VllmRunSpec, run as vllm_run

    spec = VllmRunSpec(
        max_num_seqs=cfg["max_num_seqs"],
        max_num_batched_tokens=cfg["max_num_batched_tokens"],
        model=args.model or "Qwen/Qwen2.5-1.5B-Instruct",
        port=args.port,
        num_requests=args.num_requests,
        concurrency=args.concurrency,
        max_tokens=args.max_tokens,
        tensor_parallel_size=args.tp,
        slo_ttft_p90_s=args.slo_ttft_p90_s,
        slo_tpot_p90_s=args.slo_tpot_p90_s,
    )
    return vllm_run(spec, study=study_name, trial=trial_number)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Optuna 调优推理引擎参数（S2 2 维 / S5 4 维三臂）")
    p.add_argument("--backend", choices=["vidur", "vllm"], default="vidur")
    p.add_argument("--space-mode", choices=["2d", "5d", "6d"], default="2d",
                   help="5d = mns × mtib × block_size × watermark（S5）；6d = 5d + 显式 num_blocks（P4 维度扩展）")
    p.add_argument("--arm", choices=["N", "M", "A", "S"], default="M",
                   help="N=无约束 / M=人工约束 / A=自动约束（S5）/ S=SCOOT 式（人工规则+在线边界学习，P6+）")
    p.add_argument("--n-trials", type=int, default=20)
    p.add_argument("--timeout-s", type=int, default=0, help="总超时（秒），0=不限")
    p.add_argument("--study-name", default="s2-vidur-smoke")
    p.add_argument("--sampler", choices=["tpe", "random"], default="tpe")
    p.add_argument("--seed", type=int, default=42)
    # 搜索空间
    p.add_argument("--seq-min", type=int, default=DEFAULT_SPACE["seq_min"])
    p.add_argument("--seq-max", type=int, default=DEFAULT_SPACE["seq_max"])
    p.add_argument("--tokens-min", type=int, default=1024,
                   help="mtib 采样下界（默认 1024：执行中发现的负载约束——"
                        "Vidur vllm(V0) 语义下必须 ≥ 请求最大 prefill，否则请求饿死）")
    p.add_argument("--tokens-max", type=int, default=DEFAULT_SPACE["tokens_max"])
    p.add_argument("--block-sizes", type=int, nargs="+", default=[16],
                   help="block_size 候选；注意：Vidur 内置 profiling 数据仅含 block_size=16，"
                        "其它值会因预测器训练数据为空而失败（仿真器限制，非真实引擎限制）")
    p.add_argument("--wm-min", type=float, default=0.001, help="watermark_blocks_fraction 下界")
    p.add_argument("--wm-max", type=float, default=0.2, help="watermark_blocks_fraction 上界（<1）")
    # P4：6d 的 num_blocks 维度
    p.add_argument("--nb-min", type=int, default=512, help="6d：num_blocks 采样下界")
    p.add_argument("--nb-max", type=int, default=32768, help="6d：num_blocks 采样上界")
    p.add_argument("--max-tokens-per-request", type=int, default=1024,
                   help="请求最大 token 数（6d 容量约束：num_blocks ≥ ceil(max_tokens/block_size) × mns）")
    # 工作负载 / 硬件
    p.add_argument("--device", default="a100")
    p.add_argument("--model", default=None)
    p.add_argument("--tp", type=int, default=1)
    p.add_argument("--pp", type=int, default=1)
    p.add_argument("--qps", type=float, default=8.0)
    p.add_argument("--num-requests", type=int, default=256)
    p.add_argument("--length-trace", default="splitwise_conv.csv")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--max-tokens", type=int, default=128)
    p.add_argument("--slo-ttft-p90-s", type=float, default=2.0)
    p.add_argument("--slo-tpot-p90-s", type=float, default=0.2)
    p.add_argument("--dry-run", action="store_true", help="只打印采样点，不跑仿真")
    p.add_argument("--no-constraint", action="store_true",
                   help="（2d 兼容）等价 --arm N")
    p.add_argument("--invalid-cost-units", type=float, default=3.0,
                   help="非法试验的成本当量（单位=合法试验耗时；默认 3.0）")
    p.add_argument("--sampler-graph", default=None,
                   help="P5：约束图 JSON（逗号分隔可多个）；设置后 M/A 臂改用通用 ConstraintSampler 自动注入")
    args = p.parse_args(argv)

    if args.no_constraint and args.arm == "M":
        args.arm = "N"

    cs = None
    if args.sampler_graph:
        from .constraint_sampler import ConstraintSampler, load_graph
        _constraints = []
        for _pth in args.sampler_graph.split(","):
            _pth = _pth.strip()
            if _pth:
                _constraints.extend(load_graph(_pth))
        cs = ConstraintSampler(_constraints)
        print(f"[P5] ConstraintSampler 已加载：{len(_constraints)} 条约束（数据驱动注入）")

    # SCOOT 式在线学习状态（arm=S）
    s_state = {"floor": 0, "n_learned": 0}

    import optuna
    from optuna.trial import TrialState

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def sample_cfg(trial: "optuna.Trial") -> Dict[str, Any]:
        """按空间模式与臂采样一组配置。"""
        if cs is not None and args.arm in ("M", "A"):
            spec: Dict[str, Any] = {
                "max_num_seqs": {"kind": "int", "lo": args.seq_min, "hi": args.seq_max, "log": True},
                "max_num_batched_tokens": {"kind": "int", "lo": args.seq_min, "hi": args.tokens_max, "log": True},
            }
            if args.space_mode in ("5d", "6d"):
                spec["block_size"] = {"kind": "categorical", "choices": args.block_sizes}
                spec["watermark_blocks_fraction"] = {"kind": "float",
                                                     "lo": args.wm_min, "hi": args.wm_max, "log": True}
            if args.space_mode == "6d":
                spec["num_blocks"] = {"kind": "int", "lo": args.nb_min, "hi": args.nb_max, "log": True}
            order = [k for k in ("max_num_seqs", "max_num_batched_tokens", "block_size",
                                 "watermark_blocks_fraction", "num_blocks") if k in spec]
            sampled = cs.sample(trial, spec, order=order)
            if sampled is not None:
                return sampled
            # 不可满足 → 退化为无约束采样（该 trial 会被计为非法）
        cfg: Dict[str, Any] = {}
        mns = trial.suggest_int("max_num_seqs", args.seq_min, args.seq_max, log=True)
        cfg["max_num_seqs"] = mns
        if args.space_mode in ("5d", "6d"):
            cfg["block_size"] = trial.suggest_categorical("block_size", args.block_sizes)
            cfg["watermark_blocks_fraction"] = trial.suggest_float(
                "watermark_blocks_fraction", args.wm_min, args.wm_max, log=True)
        if args.space_mode == "6d":
            # P4 第六维：KV 块数。容量约束（自动约束组的采样下界）：
            #   num_blocks ≥ ceil(max_tokens_per_request / block_size) × max_num_seqs
            #   —— 保证每个并发序列都有足额 KV 块、不触发抢占/饿死（真实 vLLM 容量规则）
            blocks_per_seq = max(1, math.ceil(args.max_tokens_per_request / args.block_sizes[0]))
            if args.arm == "N":
                cfg["num_blocks"] = trial.suggest_int("num_blocks", args.nb_min, args.nb_max, log=True)
            else:
                nb_lo = min(args.nb_max, max(args.nb_min, blocks_per_seq * mns))
                cfg["num_blocks"] = trial.suggest_int("num_blocks", nb_lo, args.nb_max, log=True)
        if args.arm == "N":
            cfg["max_num_batched_tokens"] = trial.suggest_int(
                "max_num_batched_tokens", args.seq_min, args.tokens_max, log=True)
        elif args.arm == "S":
            # SCOOT 式在线学习：仅人工规则 mtib ≥ mns + 从失败中学习的下界
            lo = max(mns, s_state["floor"])
            cfg["max_num_batched_tokens"] = trial.suggest_int(
                "max_num_batched_tokens", lo, args.tokens_max, log=True)
        else:  # M / A：约束作为采样下界（剪枝的雏形）
            cfg["max_num_batched_tokens"] = trial.suggest_int(
                "max_num_batched_tokens", max(mns, args.tokens_min), args.tokens_max, log=True)
        return cfg

    study_dir = ensure_dir(records_dir() / "optuna")
    storage = "sqlite:///" + (study_dir / "studies.db").as_posix()

    if args.dry_run:
        sampler = optuna.samplers.RandomSampler(seed=args.seed)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        for _ in range(args.n_trials):
            trial = study.ask()
            cfg = sample_cfg(trial)
            violated = cfg["max_num_batched_tokens"] < max(cfg["max_num_seqs"], args.tokens_min)
            flag = "  <- 违反约束" if violated else ""
            print(f"{cfg}{flag}")
        return 0

    sampler = (
        optuna.samplers.TPESampler(seed=args.seed, n_startup_trials=min(5, max(1, args.n_trials // 3)))
        if args.sampler == "tpe"
        else optuna.samplers.RandomSampler(seed=args.seed)
    )

    study = optuna.create_study(
        study_name=args.study_name,
        storage=storage,
        direction="maximize",
        load_if_exists=True,
        sampler=sampler,
    )

    constraint_desc = {
        "N": "无（S5 组①）",
        "M": "max_num_batched_tokens >= max(max_num_seqs, tokens_min)（SCOOT 式人工约束）",
        "A": "max_num_batched_tokens >= max(max_num_seqs, tokens_min)（自动约束图投影；加水印/块大小已验证域）",
        "S": "SCOOT 式：人工规则 mtib≥mns + 在线边界学习（失败后抬高下界，P6+）",
    }[args.arm]
    print(f"study={args.study_name} backend={args.backend} arm={args.arm} space={args.space_mode} storage={storage}")
    print(f"搜索空间: max_num_seqs∈[{args.seq_min},{args.seq_max}](log), "
          f"max_num_batched_tokens∈[{'seq_min' if args.arm == 'N' else 'max(seqs,' + str(args.tokens_min) + ')'},{args.tokens_max}](log)"
          + (f", block_size∈{args.block_sizes}, watermark∈[{args.wm_min},{args.wm_max}](log)"
             if args.space_mode == "5d" else ""))
    print(f"约束({args.arm}): {constraint_desc}；非法成本当量={args.invalid_cost_units}")

    def objective(trial: "optuna.Trial") -> float:
        cfg = sample_cfg(trial)
        if cs is not None:
            constraint_violated = not cs.satisfies(cfg)
        else:
            constraint_violated = cfg["max_num_batched_tokens"] < max(cfg["max_num_seqs"], args.tokens_min)

        record = _run_backend(args, cfg, args.study_name, trial.number)

        # 成本模型（方案文档层 3）：合法试验 = 1 单位；非法/失败试验 = 1 + c_invalid 单位
        invalid = bool(constraint_violated or record.status != "ok")
        record.metrics["constraint_violated"] = constraint_violated
        record.metrics["failed_run"] = record.status != "ok"

        # SCOOT 式在线学习（arm=S）：失败 → 抬高 mtib 下界（单调边界学习）
        if args.arm == "S" and record.status != "ok":
            s_state["floor"] = max(s_state["floor"], int(cfg["max_num_batched_tokens"]) + 1)
            s_state["n_learned"] += 1
        record.cost["experiment_units"] = round(
            1.0 + (args.invalid_cost_units if invalid else 0.0), 3)

        append_record(record, records_dir())
        print(f"  trial {trial.number:>3}: {summarize(record.to_dict())}")

        trial.set_user_attr("run_id", record.run_id)
        trial.set_user_attr("status", record.status)
        trial.set_user_attr("constraint_violated", constraint_violated)
        trial.set_user_attr("experiment_units", record.cost["experiment_units"])
        if args.arm == "S":
            trial.set_user_attr("learned_floor", s_state["floor"])
        for key, name in (("block_size", "block_size"),
                          ("watermark_blocks_fraction", "watermark_blocks_fraction")):
            if key in cfg:
                trial.set_user_attr(name, cfg[key])
        for key in ("ttft_p90_s", "tpot_p90_s", "throughput_rps", "goodput_rps", "slo_ok"):
            if key in record.metrics:
                trial.set_user_attr(key, record.metrics[key])
        if record.status != "ok":
            return 0.0
        return float(record.metrics.get("score") or 0.0)

    try:
        # 续跑语义：--n-trials 视为"目标总 trials 数"（已有 study 时只补差额）
        n_existing = len(study.trials)
        n_run = max(0, args.n_trials - n_existing)
        if n_run <= 0:
            print(f"study 已有 {n_existing} trials ≥ 目标 {args.n_trials}，跳过运行")
        else:
            print(f"续跑：已有 {n_existing} trials，再跑 {n_run} 个（目标总数 {args.n_trials}）")
            study.optimize(objective, n_trials=n_run,
                           timeout=(args.timeout_s or None))
    except KeyboardInterrupt:
        print("\n手动中断，保存已有结果")

    # ---- 保存与汇报 ----
    out_dir = ensure_dir(study_dir / args.study_name)
    trials_csv = out_dir / "trials.csv"
    study.trials_dataframe().to_csv(trials_csv, index=False, encoding="utf-8-sig")

    done = [t for t in study.trials if t.state == TrialState.COMPLETE]
    best: Dict[str, Any] = {
        "study_name": args.study_name,
        "arm": args.arm,
        "space_mode": args.space_mode,
        "n_trials": len(study.trials),
        "n_complete": len(done),
        "space": {k: getattr(args, k) for k in ("seq_min", "seq_max", "tokens_min", "tokens_max",
                                                 "block_sizes", "wm_min", "wm_max")},
        "constraint": constraint_desc,
        "invalid_cost_units": args.invalid_cost_units,
        "n_constraint_violated": sum(
            1 for t in study.trials if t.user_attrs.get("constraint_violated")),
        "n_failed": sum(
            1 for t in study.trials if t.user_attrs.get("status") not in (None, "ok")),
        "total_experiment_units": round(
            sum(float(t.user_attrs.get("experiment_units") or 0.0) for t in study.trials), 3),
    }
    if done:
        bt = study.best_trial
        best.update({
            "best_trial": bt.number,
            "best_value": bt.value,
            "best_params": bt.params,
            "best_run_id": bt.user_attrs.get("run_id"),
            "best_metrics": {k: bt.user_attrs.get(k) for k in
                             ("ttft_p90_s", "tpot_p90_s", "throughput_rps", "goodput_rps", "slo_ok")},
        })
        print(f"\n最优 trial {bt.number}: score(goodput_rps)={bt.value:.4f} {bt.params}")
    else:
        print("\n没有完成的 trial")
    (out_dir / "best.json").write_text(json.dumps(best, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"trials.csv → {trials_csv}")
    print(f"best.json  → {out_dir / 'best.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
