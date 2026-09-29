"""Vidur 仿真后端（本机可用，CPU 即可）。

为什么用 Vidur：
    本机 GPU 为 GTX 1050（compute capability 6.1，2GB 显存），
    低于 vLLM 官方要求（CC >= 7.5，见代码/README.md 的"GPU 判定"一节），
    因此按研究计划预案改用 Vidur 仿真器。

参数映射（vLLM → Vidur vllm 调度器）：
    max-num-seqs            → vllm_scheduler_config_batch_size_cap
    max-num-batched-tokens  → vllm_scheduler_config_max_tokens_in_batch

注意：Vidur 的 `vllm` 调度器对应 vLLM V0（paged attention，无 chunked prefill）；
      chunked-prefill 语义由 `sarathi` 调度器覆盖（chunk_size 即 chunk 大小）。
"""
from __future__ import annotations

import atexit
import math
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..paths import canonical_vidur_dir, ensure_dir, records_dir, vidur_dir, windows_path
from ..record import RunRecord, collect_environment, new_run_id

# ---------------------------------------------------------------------------
# 预设（写进记录，保证可对比）
# ---------------------------------------------------------------------------

DEFAULT_TRACE = "splitwise_conv.csv"


@dataclass
class VidurRunSpec:
    """一条仿真配置（两个被调参 + 固定工作负载/硬件设定）。"""

    # --- 被调参数（与 vLLM 参数一一对应） ---
    max_num_seqs: int = 64
    max_num_batched_tokens: int = 2048
    # S5 扩展维度（映射见 to_config_dict；Vidur BaseReplicaSchedulerConfig 字段）
    block_size: int = 16
    watermark_blocks_fraction: float = 0.01
    num_blocks: Optional[int] = None

    # --- 固定项 ---
    device: str = "a100"                          # a40 | a100 | h100
    model: str = "meta-llama/Llama-2-7b-hf"
    tp: int = 1
    pp: int = 1
    num_replicas: int = 1
    qps: float = 8.0
    num_requests: int = 256
    length_trace: str = DEFAULT_TRACE             # data/processed_traces 下的文件名
    # 单请求总 token 上限（prefill+decode 按比例缩放后不超此值）。
    # ⚠️ 与 vllm（V0）调度器的硬约束：max_num_batched_tokens 必须 ≥ 请求 prefill 长度，
    #    否则队列头请求永远排不进去 → 整条队列饿死（simulator.py:78 断言）。
    #    默认 1024 与 mtib 默认值 2048 配套；改大时请同步调大 mtib。
    max_tokens_per_request: int = 1024
    seed: int = 42
    slo_ttft_p90_s: float = 2.0
    slo_tpot_p90_s: float = 0.2
    predictor: str = "random_forrest"             # random_forrest | linear_regression
    # 预测器训练配置：默认"单组合"（比默认网格 3×3×3 快 ~27 倍；实测 MEAP ~1%）
    # 需要完整网格做消融时设 predictor_full_grid=True
    predictor_full_grid: bool = False
    predictor_num_estimators: int = 10
    predictor_max_depth: int = 16
    predictor_min_samples_split: int = 2
    # 预测范围（必须覆盖实际会出现的配置，否则 KeyError）。
    # ⚠️ 这些值必须由"搜索空间上界"决定（跨 trial 常量），不能随单个 trial 的参数变化，
    #    否则每个 trial 的预测器配置都不同 → 缓存全部失效，每次都要重训。
    #   predictor_max_tokens_in_batch ≥ 搜索空间的 max_num_batched_tokens 上界
    #   predictor_max_prefill_chunk  ≥ 批内 prefill 聚合上界（自动按 √(max_tokens×mtib) 推导）
    #   predictor_max_batch_size     ≥ 搜索空间的 max_num_seqs 上界
    predictor_max_tokens_in_batch: int = 8192
    predictor_max_prefill_chunk: int = 1024
    predictor_max_batch_size: int = 512
    # --- 记录用元信息 ---
    keep_failed: bool = True

    def to_config_dict(self) -> Dict[str, Any]:
        cfg = asdict(self)
        cfg.pop("keep_failed", None)
        cfg["scheduler"] = "vllm"
        cfg["length_trace"] = Path(self.length_trace).name
        cfg["sim_param_mapping"] = {
            "max_num_seqs": "vllm_scheduler_config_batch_size_cap",
            "max_num_batched_tokens": "vllm_scheduler_config_max_tokens_in_batch",
            "block_size": "vllm_scheduler_config_block_size",
            "watermark_blocks_fraction": "vllm_scheduler_config_watermark_blocks_fraction",
            "num_blocks": "vllm_scheduler_config_num_blocks",
        }
        cfg["constraints_applied"] = (
            ["max_num_batched_tokens >= max_num_seqs"]
            if self.max_num_batched_tokens >= self.max_num_seqs
            else []
        )
        cfg["constraint_note"] = (
            "vllm(V0) 调度器还有一条负载相关硬约束："
            "max_num_batched_tokens >= 单请求最大 prefill token 数，否则请求饿死；"
            f"本负载 max_tokens_per_request={self.max_tokens_per_request}"
        )
        return cfg


# ---------------------------------------------------------------------------
# 预测器进程内缓存：把 RF 训练成本从"每次 Simulator 构造"降为"每进程一次"
# 安全性依据：预测器只读取 replica_scheduler_config 的*类型*（vllm/orca/...），
#             与 batch_size_cap / max_tokens_in_batch 无关
#             （见 vidur/execution_time_predictor/base_execution_time_predictor.py:25）
# ---------------------------------------------------------------------------

_CACHE_INSTALLED = False


def _install_lightweight_stubs() -> None:
    """跳过 wandb / plotly_express 的重量级导入（实测本机合计约 30s/进程）。

    安全性：Vidur 只在两类我们都不走的路径里用它们——
      - wandb：仅当 `wandb.run` 非空（需登录/联网）或设置了 wandb_project 时；
      - plotly_express：仅在 store_plots=True 生成 PNG 时（我们统一关闭）。
    需要真实绘图/上报时，设 AGENTOPS_REAL_WANDB=1 / AGENTOPS_REAL_PLOTLY=1。
    """
    import types

    if os.environ.get("AGENTOPS_REAL_WANDB") != "1" and "wandb" not in sys.modules:
        wb = types.ModuleType("wandb")
        wb.run = None

        def _noop(*args, **kwargs):
            return None

        wb.log = _noop
        wb.init = _noop
        wb.plot = types.SimpleNamespace(line=_noop, bar=_noop)

        class _Table(dict):
            def __init__(self, *args, **kwargs):
                super().__init__()

        wb.Table = _Table
        sys.modules["wandb"] = wb

    if os.environ.get("AGENTOPS_REAL_PLOTLY") != "1" and "plotly_express" not in sys.modules:
        px = types.ModuleType("plotly_express")

        def _plot_unavailable(*args, **kwargs):
            raise RuntimeError(
                "plotly_express 已被 AgentOps 轻量替换（S2 提速）；"
                "如需真实绘图请设置 AGENTOPS_REAL_PLOTLY=1")

        px.line = _plot_unavailable
        px.scatter = _plot_unavailable
        px.bar = _plot_unavailable
        px.histogram = _plot_unavailable
        sys.modules["plotly_express"] = px


def _ensure_vidur_on_path() -> Path:
    """把 Vidur 仓库根加进 sys.path。

    不依赖 pip editable 安装（uv/setuptools 生成的 finder 可能是空映射），
    同时保证运行的永远是仓库里这份源码（与研究记录的 git commit 一致）。
    """
    repo = vidur_dir().resolve()
    repo_str = str(repo)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    return repo


def _reset_vidur_entity_counters() -> None:
    """每次创建 Simulator 前重置实体 id 计数器。

    Vidur 的实体 id 来自类级计数器 `BaseEntity._id`（只为 CLI 单次运行设计），
    而 RoundRobinGlobalScheduler.schedule() 用 0-based 索引引用 replica：
    同一进程跑第二个仿真时 replica id 变成 1、2、... → `KeyError: 0`。
    本函数让"单进程多 trial"（Optuna）可以复用预测器缓存而不必每 trial 起进程。
    """
    try:
        import vidur.entities as entities
        from vidur.entities.base_entity import BaseEntity

        targets = [BaseEntity]
        targets += [
            obj for obj in vars(entities).values()
            if isinstance(obj, type) and issubclass(obj, BaseEntity)
        ]
        for cls in targets:
            if "_id" in cls.__dict__:
                cls._id = -1
    except Exception:
        pass


def _install_predictor_cache() -> None:
    global _CACHE_INSTALLED
    if _CACHE_INSTALLED:
        return

    _ensure_vidur_on_path()
    _install_lightweight_stubs()

    from vidur.execution_time_predictor.execution_time_predictor_registry import (
        ExecutionTimePredictorRegistry,
    )

    original_get = ExecutionTimePredictorRegistry.get.__func__
    cache: Dict[Tuple[Any, ...], Any] = {}

    def cached_get(cls, key, *args, **kwargs):
        predictor_config = kwargs.get("predictor_config")
        replica_config = kwargs.get("replica_config")
        scheduler_config = kwargs.get("replica_scheduler_config")
        scheduler_kind = getattr(getattr(scheduler_config, "get_type", lambda: "")(), "name", "")
        cache_key = (key, repr(predictor_config), repr(replica_config), str(scheduler_kind))
        if cache_key not in cache:
            cache[cache_key] = original_get(cls, key, *args, **kwargs)
        return cache[cache_key]

    ExecutionTimePredictorRegistry.get = classmethod(cached_get)
    _CACHE_INSTALLED = True


# ---------------------------------------------------------------------------
# 组装 Vidur CLI 参数
# ---------------------------------------------------------------------------

def _build_cli_args(spec: VidurRunSpec, out_dir: Path) -> List[str]:
    trace_path = vidur_dir() / "data" / "processed_traces" / spec.length_trace
    if not trace_path.exists():
        raise FileNotFoundError(f"找不到 trace 文件: {trace_path}")

    predictor_prefix = f"{spec.predictor}_execution_time_predictor_config"
    if spec.predictor_full_grid:
        estimators, depths, min_splits = "250 500 750", "8 16 32", "2 5 10"
    else:
        estimators = str(spec.predictor_num_estimators)
        depths = str(spec.predictor_max_depth)
        min_splits = str(spec.predictor_min_samples_split)
    # 预测范围必须覆盖真实配置，否则 KeyError；只用"空间上界"（跨 trial 常量）推导，
    # 保证同一 study 内预测器配置不变 → 缓存可复用
    pred_max_tokens = max(spec.predictor_max_tokens_in_batch, spec.max_tokens_per_request + 8)
    # 批内 prefill 聚合 = √(Σc_i²) ≤ √(max_c × Σc_i) ≤ √(max_tokens_per_request × mtib上界)
    agg_prefill_bound = math.ceil(math.sqrt(max(spec.max_tokens_per_request, 1)
                                            * max(spec.predictor_max_tokens_in_batch, 1)))
    pred_max_chunk = max(spec.predictor_max_prefill_chunk, agg_prefill_bound + 8)
    pred_max_batch = max(spec.predictor_max_batch_size, spec.max_num_seqs)
    args: List[str] = [
        "--seed", str(spec.seed),
        "--replica_config_device", spec.device,
        "--replica_config_model_name", spec.model,
        "--replica_config_tensor_parallel_size", str(spec.tp),
        "--replica_config_num_pipeline_stages", str(spec.pp),
        "--cluster_config_num_replicas", str(spec.num_replicas),
        "--request_generator_config_type", "synthetic",
        "--synthetic_request_generator_config_num_requests", str(spec.num_requests),
        "--length_generator_config_type", "trace",
        "--trace_request_length_generator_config_trace_file", str(trace_path),
        "--trace_request_length_generator_config_max_tokens", str(spec.max_tokens_per_request),
        "--interval_generator_config_type", "poisson",
        "--poisson_request_interval_generator_config_qps", str(spec.qps),
        "--replica_scheduler_config_type", "vllm",
        "--vllm_scheduler_config_batch_size_cap", str(spec.max_num_seqs),
        "--vllm_scheduler_config_max_tokens_in_batch", str(spec.max_num_batched_tokens),
        "--vllm_scheduler_config_block_size", str(spec.block_size),
        "--vllm_scheduler_config_watermark_blocks_fraction", str(spec.watermark_blocks_fraction),
        "--execution_time_predictor_config_type", spec.predictor,
        f"--{predictor_prefix}_num_estimators", *estimators.split(),
        f"--{predictor_prefix}_max_depth", *depths.split(),
        f"--{predictor_prefix}_min_samples_split", *min_splits.split(),
        f"--{predictor_prefix}_prediction_max_batch_size", str(pred_max_batch),
        f"--{predictor_prefix}_prediction_max_prefill_chunk_size", str(pred_max_chunk),
        f"--{predictor_prefix}_prediction_max_tokens_per_request", str(pred_max_tokens),
        "--metrics_config_output_dir", str(out_dir),
        "--no-metrics_config_store_plots",           # 跳过 PNG 生成（本机无显示，且慢）
        "--no-metrics_config_enable_chrome_trace",   # 关闭 chrome trace（体积大，S2 用不上）
        "--metrics_config_store_token_completion_metrics",  # 记录逐 token ITL 的 CSV
    ]
    if spec.num_blocks is not None:
        args += ["--vllm_scheduler_config_num_blocks", str(spec.num_blocks)]
    return args


@contextmanager
def _chdir(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


# ---------------------------------------------------------------------------
# 运行 + 指标提取
# ---------------------------------------------------------------------------

def _as_config(spec: VidurRunSpec, output_base: Path):
    """用 Vidur 自己的 CLI 解析器构造 SimulationConfig（与官方入口一致）。

    Vidur 会在 output_base 下再建一个时间戳子目录，返回的 cfg 里带真实目录。
    调用方需保证 CWD 已在 Vidur 仓库根目录（相对路径 data/... 依赖它）。
    """
    _ensure_vidur_on_path()
    from vidur.config import SimulationConfig

    args = _build_cli_args(spec, output_base)
    old_argv = sys.argv
    sys.argv = ["agentops-vidur"] + args
    try:
        cfg = SimulationConfig.create_from_cli_args()
    finally:
        sys.argv = old_argv
    return cfg


def _request_pairs(store, metric_enum) -> List[Tuple[Any, float]]:
    try:
        return list(store._request_metrics_time_distributions[metric_enum]._data_series)
    except Exception:
        return []


def _hist_pairs(store, metric_enum) -> List[Tuple[Any, float]]:
    try:
        return list(store._request_metrics_histogram[metric_enum]._data_series)
    except Exception:
        return []


def _percentiles(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {"p50": None, "p90": None, "p99": None, "mean": None}
    arr = np.asarray(values, dtype=float)
    return {
        "p50": round(float(np.percentile(arr, 50)), 4),
        "p90": round(float(np.percentile(arr, 90)), 4),
        "p99": round(float(np.percentile(arr, 99)), 4),
        "mean": round(float(arr.mean()), 4),
    }


def _extract_metrics(sim, spec: VidurRunSpec) -> Dict[str, Any]:
    """从 Vidur 的 MetricsStore 提取指标（TTFT / TPOT / ITL / E2E / 吞吐 / SLO）。"""
    from vidur.metrics.constants import (
        RequestCompletionMetricsTimeSeries as C,
        RequestMetricsHistogram as H,
        RequestMetricsTimeDistributions as R,
        TokenMetricsTimeDistribution as T,
    )

    store = sim._metric_store
    ttft = dict(_request_pairs(store, R.PREFILL_TIME_E2E))
    tpot = dict(_request_pairs(store, R.DECODE_TIME_EXECUTION_PLUS_PREEMPTION_NORMALIZED))
    e2e = dict(_request_pairs(store, R.REQUEST_E2E_TIME))
    restarts = dict(_hist_pairs(store, H.REQUEST_NUM_RESTARTS))
    decode_tokens = dict(_hist_pairs(store, H.REQUEST_DECODE_TOKENS))

    arrivals = list(store._request_completion_metrics_time_series[C.REQUEST_ARRIVAL]._data_series)
    completions = list(store._request_completion_metrics_time_series[C.REQUEST_COMPLETION]._data_series)

    # 逐 token ITL：ddsketch 分位数（失败时把原因写进 itl_error，不静默）
    itl: Dict[str, Any] = {"p50": None, "p90": None, "p99": None}
    try:
        # 注意：Vidur 的枚举名有拼写错误（PREMPTION，少一个 E），照抄它
        sketch = store._token_metrics_time_distribution[
            T.DECODE_TOKEN_EXECUTION_PLUS_PREMPTION_TIME  # noqa: E501 - Vidur typo
        ]._sketch
        if sketch.count > 0:
            itl = {
                "p50": round(float(sketch.get_quantile_value(0.5)), 4),
                "p90": round(float(sketch.get_quantile_value(0.9)), 4),
                "p99": round(float(sketch.get_quantile_value(0.99)), 4),
            }
        else:
            itl["error"] = "sketch.count == 0"
    except Exception as exc:  # noqa: BLE001
        itl["error"] = f"{type(exc).__name__}: {exc}"

    n_completed = len(completions)
    if arrivals and completions:
        makespan = max(0.0, max(x for x, _ in completions) - min(x for x, _ in arrivals))
    else:
        makespan = 0.0
    makespan = max(makespan, 1e-9)

    total_decode_tokens = int(sum(decode_tokens.values())) if decode_tokens else 0
    ttft_stats, tpot_stats, e2e_stats = _percentiles(list(ttft.values())), _percentiles(list(tpot.values())), _percentiles(list(e2e.values()))

    slo_ok = bool(
        ttft_stats["p90"] is not None
        and tpot_stats["p90"] is not None
        and ttft_stats["p90"] <= spec.slo_ttft_p90_s
        and tpot_stats["p90"] <= spec.slo_tpot_p90_s
    )
    good = sum(
        1
        for rid, t in tpot.items()
        if ttft.get(rid, 1e9) <= spec.slo_ttft_p90_s and t <= spec.slo_tpot_p90_s
    )

    metrics: Dict[str, Any] = {
        "completed_requests": n_completed,
        "makespan_s": round(makespan, 4),
        "sim_time_s": round(float(sim._time), 4),
        "throughput_rps": round(n_completed / makespan, 6),
        "output_token_throughput": round(total_decode_tokens / makespan, 4),
        "total_decode_tokens": total_decode_tokens,
        "ttft_p50_s": ttft_stats["p50"],
        "ttft_p90_s": ttft_stats["p90"],
        "ttft_p99_s": ttft_stats["p99"],
        "tpot_p50_s": tpot_stats["p50"],
        "tpot_p90_s": tpot_stats["p90"],
        "tpot_p99_s": tpot_stats["p99"],
        "itl_p50_s": itl["p50"],
        "itl_p90_s": itl["p90"],
        "itl_p99_s": itl["p99"],
        "itl_error": itl.get("error"),
        "e2e_p50_s": e2e_stats["p50"],
        "e2e_p90_s": e2e_stats["p90"],
        "e2e_p99_s": e2e_stats["p99"],
        "slo_ttft_p90_s": spec.slo_ttft_p90_s,
        "slo_tpot_p90_s": spec.slo_tpot_p90_s,
        "slo_ok": slo_ok,
        "goodput_rps": round(good / makespan, 6),        # 满足逐请求 SLO 的请求/秒
        "slo_met_requests": good,
        "restarts_mean": round(float(np.mean(list(restarts.values()))), 4) if restarts else 0.0,
        "restarts_max": int(max(restarts.values())) if restarts else 0,
        "score": round(good / makespan, 6),              # Optuna 目标（最大化）
    }
    return metrics


def run(spec: VidurRunSpec, *, study: Optional[str] = None,
        trial: Optional[int] = None) -> RunRecord:
    """跑通"一条配置"的完整链路，返回一条 RunRecord（并写入成本/环境信息）。"""
    run_id = new_run_id("vidur")
    record = RunRecord(run_id=run_id, backend="vidur_sim", mode="simulate",
                       study=study, trial=trial)
    record.config = spec.to_config_dict()
    record.environment = collect_environment(
        backend="vidur", backend_repo=canonical_vidur_dir(),
        extra={
            "simulator": "vidur",
            "runtime_repo": str(vidur_dir()),
            "note": "CPU 仿真；无真实 GPU 消耗",
        },
    )
    out_dir = ensure_dir(records_dir() / "仿真输出")
    record.artifacts = {"output_dir_base": str(out_dir)}
    run_out_dir: Optional[Path] = None

    t0 = time.perf_counter()
    try:
        _install_predictor_cache()

        from vidur.simulator import Simulator
        from vidur.utils.random import set_seeds

        # 注意：Vidur 的预测器数据用相对路径 ./data/...，整段仿真必须在仓库根目录下执行
        with _chdir(vidur_dir()):
            cfg = _as_config(spec, out_dir)
            run_out_dir = Path(cfg.metrics_config.output_dir)   # Vidur 生成的时间戳目录
            record.artifacts["output_dir"] = str(run_out_dir)
            record.artifacts["output_dir_windows"] = windows_path(run_out_dir)

            t_setup0 = time.perf_counter()
            set_seeds(cfg.seed)
            _reset_vidur_entity_counters()
            sim = Simulator(cfg)
            setup_s = time.perf_counter() - t_setup0

            t_solve0 = time.perf_counter()
            sim.run()
            solve_s = time.perf_counter() - t_solve0

            atexit.unregister(sim._write_output)   # 避免退出时重复写盘
            try:
                sim._metric_store.plot()
            except Exception:
                pass

            record.metrics = _extract_metrics(sim, spec)
            sim_seconds = float(sim._time)
        n_devices = spec.tp * spec.pp * spec.num_replicas
        record.cost = {
            "wall_clock_s": round(time.perf_counter() - t0, 3),
            "setup_s": round(setup_s, 3),
            "solve_s": round(solve_s, 3),
            "sim_seconds": round(sim_seconds, 3),
            "n_gpus_used": 0,                                    # 仿真：不占真实 GPU
            "gpu_hours": 0.0,                                    # 论文口径：真实 GPU 小时
            "gpu_hours_if_real": round(sim_seconds * n_devices / 3600.0, 6),
            "llm_tokens": 0,
            "note": "gpu_hours_if_real = 仿真时间 × 设备数 / 3600（若真实部署该负载的估算）",
        }
        record.status = "ok"
    except Exception as exc:  # noqa: BLE001 —— 失败也要记录，供后续分析非法配置
        import traceback

        record.status = "failed"
        message = f"{type(exc).__name__}: {exc}".strip()
        if isinstance(exc, AssertionError) and not str(exc):
            message += (
                " （空断言，常见于请求饿死：max_num_batched_tokens 小于请求 prefill 长度，"
                "或显存/块数不足；见 vidur/simulator.py:78 与 vllm_replica_scheduler.py）"
            )
        record.error = message
        record.artifacts["traceback"] = traceback.format_exc()[-4000:]
        record.cost.setdefault("wall_clock_s", round(time.perf_counter() - t0, 3))
        record.cost.setdefault("gpu_hours", 0.0)
        record.cost.setdefault("n_gpus_used", 0)

    # 每次运行都落一份完整记录副本，便于单条追溯
    try:
        import json
        target = run_out_dir if run_out_dir is not None else out_dir
        (target / "agentops_record.json").write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return record
