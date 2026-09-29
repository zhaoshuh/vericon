# -*- coding: utf-8 -*-
"""S6 · Phase A：llama.cpp 真实约束证伪（构造违反参数 → 运行真实二进制 → 捕获报错）

运行（WSL）：见 run_s6_probe.sh
产出：实验记录/llamacpp_constraints.json
"""
import json
import os
import subprocess
import time

BIN = "/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194"
MODEL = "/mnt/f/文献/AgentOps/代码/third_party/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
OUT = "/mnt/f/文献/AgentOps/实验记录/llamacpp_constraints.json"
ENV = dict(os.environ)
ENV["LD_LIBRARY_PATH"] = os.path.expanduser("~/.venvs/agentops-py311/lib") + ":" + ENV.get("LD_LIBRARY_PATH", "")

# (用例名, 约束ID, 是否预期违反, 额外参数)
CASES = [
    ("L1 违反: n_ubatch(256) > n_batch(128)", "L1", True, ["-b", "128", "-ub", "256"]),
    ("L1 对照: n_ubatch(128) <= n_batch(256)", "L1", False, ["-b", "256", "-ub", "128"]),
    ("L1 边界: n_ubatch == n_batch == 256", "L1", False, ["-b", "256", "-ub", "256"]),
    ("L2 违反: keep(512) > ctx(256)", "L2", True, ["-c", "256", "--keep", "512"]),
    ("L2 对照: keep(128) <= ctx(512)", "L2", False, ["-c", "512", "--keep", "128"]),
    ("L4 违反: n_batch = 0", "L4", True, ["-b", "0"]),
    ("L4 违反: n_ubatch = 0", "L4", True, ["-ub", "0"]),
    ("L4 违反: threads = 0", "L4", True, ["-t", "0"]),
    ("L4 对照: threads = 2", "L4", False, ["-t", "2"]),
    ("L6 组合: flash-attn=on + KV q8_0", "L6", None, ["-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0"]),
    ("L6 组合: flash-attn=off + KV q8_0", "L6", True, ["-fa", "off", "-ctk", "q8_0", "-ctv", "q8_0"]),
    ("L6 组合: flash-attn=off + 仅 K q8_0", "L6", None, ["-fa", "off", "-ctk", "q8_0"]),
    ("L8 违反: prompt 超过 ctx（-c 16 长 prompt）", "L8", True, ["-c", "16", "-p", "这是一段明显超过十六个 token 的提示文本用来测试上下文长度限制行为abcdefghijklmnopqrstuvwxyz0123456789"]),
    ("L5 组合: -ngl 1（无 CUDA 构建）", "L5", None, ["-ngl", "1"]),
    ("L1 复核: ub>b 时 verbose 日志", "L1", None, ["-b", "128", "-ub", "256", "-lv", "1"]),
    ("L7 组合: load-mode=mlock（WSL/drvfs）", "L7", None, ["-lm", "mlock"]),
    ("L7 对照: load-mode=auto", "L7", False, ["-lm", "auto"]),
]


def run_case(name, cid, expect_violate, extra):
    cmd = [f"{BIN}/llama-cli", "-m", MODEL, "-p", "hi", "-n", "8", "--no-warmup", "-st"] + extra
    t0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=ENV,
                           stdin=subprocess.DEVNULL)
        code, err, out = p.returncode, p.stderr, p.stdout
    except subprocess.TimeoutExpired as e:
        code = "timeout"
        err = (e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        out = ""
    wall = round(time.perf_counter() - t0, 2)

    low = (err + out).lower()
    if code != 0 and code != "timeout":
        status = "confirmed"   # 真报错/中止
    elif "error" in low or "assert" in low or "abort" in low:
        status = "error_in_log"
    elif "warning" in low or "warn" in low:
        status = "warning"
    elif code == "timeout":
        status = "timeout"
    else:
        status = "no_error"

    return {
        "case": name, "constraint_id": cid, "expected_violation": expect_violate,
        "args": extra, "exit_code": code, "status": status, "wall_s": wall,
        "stderr_tail": err[-800:], "stdout_tail": out[-300:],
    }


def main():
    if not os.path.exists(MODEL):
        print(f"模型不存在: {MODEL}（等待下载完成）")
        return
    results = []
    for name, cid, exp, extra in CASES:
        rec = run_case(name, cid, exp, extra)
        results.append(rec)
        print(f'{rec["status"]:14s} exit={rec["exit_code"]} {name}')
        if rec["status"] in ("confirmed", "error_in_log"):
            tail = (rec["stderr_tail"] or "").strip().splitlines()
            if tail:
                print(f'     ↳ {tail[-1][:160]}')
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"engine": "llama.cpp 0.5.0-dev build 11194 (commit 9f70b2cec)",
                   "model": os.path.basename(MODEL),
                   "method": "构造违反参数 → 运行 llama-cli → 捕获 exit code / stderr",
                   "results": results}, f, ensure_ascii=False, indent=2)
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
