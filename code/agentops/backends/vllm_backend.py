"""真实 vLLM 后端（需要 Linux + GPU，CC >= 7.5）。

本机（GTX 1050 / CC 6.1 / 2GB / Windows）无法运行；本模块的作用是：
1. 把"调优两个参数 + 统一记录 + 成本核算"提前写好，等有 GPU 机器（实验室/云）时
   一条命令即可切换到真实服务；
2. 用内置假服务器做 `--selftest`，在无 GPU 的情况下验证**客户端逻辑**
   （SSE 解析、TTFT/ITL 计算、指标汇总）没有错误。

用法（GPU 机器上）：
    python -m agentops.run_one --backend vllm --max-num-seqs 64 --max-num-batched-tokens 2048
本机自检：
    python -m agentops.backends.vllm_backend --selftest
"""
from __future__ import annotations

import json
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

import numpy as np

from ..record import RunRecord, collect_environment, new_run_id


@dataclass
class VllmRunSpec:
    # --- 被调参数 ---
    max_num_seqs: int = 64
    max_num_batched_tokens: int = 2048

    # --- 固定项 ---
    model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    port: int = 8000
    num_requests: int = 64
    concurrency: int = 8
    max_tokens: int = 128
    prompt_len_buckets: tuple = (128, 256, 512)
    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.9
    enforce_eager: bool = True
    startup_timeout_s: int = 900
    request_timeout_s: int = 300
    slo_ttft_p90_s: float = 2.0
    slo_tpot_p90_s: float = 0.2

    def to_config_dict(self) -> Dict[str, Any]:
        cfg = asdict(self)
        cfg["engine"] = "vllm"
        cfg["param_mapping"] = {
            "max_num_seqs": "--max-num-seqs",
            "max_num_batched_tokens": "--max-num-batched-tokens",
        }
        cfg["constraints_applied"] = (
            ["max_num_batched_tokens >= max_num_seqs"]
            if self.max_num_batched_tokens >= self.max_num_seqs
            else []
        )
        return cfg


# ---------------------------------------------------------------------------
# 服务器启动 / 健康检查
# ---------------------------------------------------------------------------

def serve_command(spec: VllmRunSpec) -> List[str]:
    exe = shutil.which("vllm")
    cmd = [exe, "serve", spec.model] if exe else [
        sys.executable, "-m", "vllm.entrypoints.cli.main", "serve", spec.model,
    ]
    cmd += [
        "--host", "127.0.0.1",
        "--port", str(spec.port),
        "--max-num-seqs", str(spec.max_num_seqs),
        "--max-num-batched-tokens", str(spec.max_num_batched_tokens),
        "--tensor-parallel-size", str(spec.tensor_parallel_size),
        "--gpu-memory-utilization", str(spec.gpu_memory_utilization),
        "--disable-log-requests",
    ]
    if spec.enforce_eager:
        cmd.append("--enforce-eager")
    return cmd


def _wait_health(port: int, timeout_s: int, proc) -> float:
    t0 = time.perf_counter()
    url = f"http://127.0.0.1:{port}/health"
    while time.perf_counter() - t0 < timeout_s:
        if proc.poll() is not None:
            raise RuntimeError(f"vLLM 进程提前退出，returncode={proc.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    return time.perf_counter() - t0
        except Exception:
            time.sleep(2.0)
    raise TimeoutError(f"vLLM 在 {timeout_s}s 内未就绪（{url}）")


# ---------------------------------------------------------------------------
# 客户端：流式请求 + TTFT / ITL / E2E
# ---------------------------------------------------------------------------

def _make_prompts(spec: VllmRunSpec) -> List[str]:
    prompts = []
    for i in range(spec.num_requests):
        n_words = spec.prompt_len_buckets[i % len(spec.prompt_len_buckets)]
        prompts.append("请继续写完下面这段文字。" + ("the quick brown fox " * n_words).strip())
    return prompts


def stream_one(base_url: str, model: str, prompt: str, max_tokens: int,
               timeout_s: int) -> Dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "stream": True,
    }
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer dummy"},
        method="POST",
    )
    t0 = time.perf_counter()
    ttft: Optional[float] = None
    last: Optional[float] = None
    itls: List[float] = []
    n_tokens = 0
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj.get("choices", [{}])[0].get("delta", {}).get("content")
                except Exception:
                    continue
                if delta:
                    now = time.perf_counter()
                    if ttft is None:
                        ttft = now - t0
                    elif last is not None:
                        itls.append(now - last)
                    last = now
                    n_tokens += 1
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    e2e = time.perf_counter() - t0
    return {"ok": True, "ttft_s": ttft, "itls": itls, "e2e_s": e2e, "n_tokens": n_tokens}


def measure(base_url: str, spec: VllmRunSpec, prompts: List[str]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=spec.concurrency) as pool:
        results = list(pool.map(
            lambda p: stream_one(base_url, spec.model, p, spec.max_tokens, spec.request_timeout_s),
            prompts,
        ))
    makespan = max(time.perf_counter() - t0, 1e-9)

    ok = [r for r in results if r["ok"] and r["ttft_s"] is not None]
    failed = [r for r in results if not r["ok"] or r["ttft_s"] is None]
    ttft = [r["ttft_s"] for r in ok]
    itl = [x for r in ok for x in r["itls"]]
    e2e = [r["e2e_s"] for r in ok]
    tokens = sum(r.get("n_tokens", 0) for r in ok)

    def pct(values: List[float], q: float) -> Optional[float]:
        if not values:
            return None
        return round(float(np.percentile(np.asarray(values, dtype=float), q)), 4)

    ttft_p90, tpot_p90 = pct(ttft, 90), pct(itl, 90)
    good = sum(
        1 for r in ok
        if r["ttft_s"] <= spec.slo_ttft_p90_s
        and (r["itls"] and float(np.mean(r["itls"])) <= spec.slo_tpot_p90_s)
    )
    return {
        "completed_requests": len(ok),
        "failed_requests": len(failed),
        "first_error": failed[0]["error"] if failed else None,
        "makespan_s": round(makespan, 4),
        "throughput_rps": round(len(ok) / makespan, 6),
        "output_token_throughput": round(tokens / makespan, 4),
        "total_output_tokens": tokens,
        "ttft_p50_s": pct(ttft, 50), "ttft_p90_s": ttft_p90, "ttft_p99_s": pct(ttft, 99),
        "tpot_p50_s": pct(itl, 50), "tpot_p90_s": tpot_p90, "tpot_p99_s": pct(itl, 99),
        "itl_p50_s": pct(itl, 50), "itl_p90_s": pct(itl, 90), "itl_p99_s": pct(itl, 99),
        "e2e_p50_s": pct(e2e, 50), "e2e_p90_s": pct(e2e, 90), "e2e_p99_s": pct(e2e, 99),
        "slo_ttft_p90_s": spec.slo_ttft_p90_s,
        "slo_tpot_p90_s": spec.slo_tpot_p90_s,
        "slo_ok": bool(ttft_p90 is not None and tpot_p90 is not None
                       and ttft_p90 <= spec.slo_ttft_p90_s and tpot_p90 <= spec.slo_tpot_p90_s),
        "goodput_rps": round(good / makespan, 6),
        "slo_met_requests": good,
        "score": round(good / makespan, 6),
    }


# ---------------------------------------------------------------------------
# 完整跑一条配置
# ---------------------------------------------------------------------------

def run(spec: VllmRunSpec, *, study: Optional[str] = None,
        trial: Optional[int] = None) -> RunRecord:
    import subprocess

    run_id = new_run_id("vllm")
    record = RunRecord(run_id=run_id, backend="vllm", mode="serve",
                       study=study, trial=trial)
    record.config = spec.to_config_dict()
    try:
        from importlib.metadata import version as _v
        vllm_version = _v("vllm")
    except Exception:
        vllm_version = "unknown"
    record.environment = collect_environment(
        backend="vllm", extra={"engine": "vllm", "vllm_version": vllm_version, "gpu": "n/a"})

    t0 = time.perf_counter()
    proc = None
    try:
        cmd = serve_command(spec)
        record.artifacts["serve_command"] = " ".join(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        startup_s = _wait_health(spec.port, spec.startup_timeout_s, proc)

        base_url = f"http://127.0.0.1:{spec.port}"
        prompts = _make_prompts(spec)
        # 预热 1 条（排除编译/首次分配开销，不计入指标）
        stream_one(base_url, spec.model, prompts[0], 8, spec.request_timeout_s)

        metrics = measure(base_url, spec, prompts)
        uptime_s = time.perf_counter() - t0
        record.metrics = metrics
        record.cost = {
            "wall_clock_s": round(uptime_s, 3),
            "startup_s": round(startup_s, 3),
            "n_gpus_used": spec.tensor_parallel_size,
            "gpu_hours": round(uptime_s * spec.tensor_parallel_size / 3600.0, 6),
            "llm_tokens": 0,
            "note": "gpu_hours = 服务进程存活时长 × GPU 数 / 3600（含启动与预热）",
        }
        record.status = "ok" if metrics["completed_requests"] > 0 else "failed"
        if record.status == "failed":
            record.error = metrics.get("first_error") or "没有任何请求成功"
    except Exception as exc:  # noqa: BLE001
        record.status = "failed"
        record.error = f"{type(exc).__name__}: {exc}"
        record.cost = {"wall_clock_s": round(time.perf_counter() - t0, 3),
                       "n_gpus_used": 0, "gpu_hours": 0.0, "llm_tokens": 0}
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except Exception:
                proc.kill()
    return record


# ---------------------------------------------------------------------------
# 自检：假 SSE 服务器（无 GPU 验证客户端逻辑）
# ---------------------------------------------------------------------------

def _fake_server(port: int) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # 静默
            pass

        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            if not self.path.endswith("/chat/completions"):
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            n = 16
            for i in range(n):
                chunk = {
                    "choices": [{"delta": {"content": f"tok{i} "}, "finish_reason": None}],
                }
                self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                self.wfile.flush()
                time.sleep(0.002 if i else 0.05)  # 制造一个可观测的 TTFT
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def selftest() -> int:
    """无 GPU 自检：验证 SSE 解析 / TTFT / ITL / 指标汇总逻辑。"""
    port = 18123
    server = _fake_server(port)
    try:
        spec = VllmRunSpec(port=port, num_requests=6, concurrency=3, max_tokens=16,
                           startup_timeout_s=10, request_timeout_s=30)
        base_url = f"http://127.0.0.1:{port}"
        prompts = _make_prompts(spec)
        metrics = measure(base_url, spec, prompts)
        checks = {
            "6 条请求全部成功": metrics["completed_requests"] == 6,
            "TTFT 已测量": metrics["ttft_p90_s"] is not None,
            "ITL 已测量": metrics["itl_p90_s"] is not None,
            "吞吐 > 0": metrics["throughput_rps"] > 0,
        }
        for name, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'}  {name}")
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return 0 if all(checks.values()) else 1
    finally:
        server.shutdown()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    print("用法: python -m agentops.backends.vllm_backend --selftest")
    print("真实运行请用: python -m agentops.run_one --backend vllm ...")
