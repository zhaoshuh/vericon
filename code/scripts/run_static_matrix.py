# -*- coding: utf-8 -*-
"""P2/P3 静态矩阵：对 vLLM 历史版本与 SGLang 跑参数清单 + 候选扫描

输出: 实验记录/P2-版本研究/{label}-params.json / {label}-candidates.json
      实验记录/P3-sglang/{label}-params.json / {label}-candidates.json
"""
import os
import subprocess
import sys

PY = r"C:\Python311\python.exe"
SCRIPTS = r"F:\文献\AgentOps\代码\scripts"
TP = r"F:\文献\AgentOps\代码\third_party"
REC = r"F:\文献\AgentOps\实验记录"

JOBS = [
    ("v0.4.2", os.path.join(TP, "vllm-versions", "v0.4.2"), "vllm", "P2-版本研究"),
    ("v0.5.5", os.path.join(TP, "vllm-versions", "v0.5.5"), "vllm", "P2-版本研究"),
    ("v0.6.6", os.path.join(TP, "vllm-versions", "v0.6.6"), "vllm", "P2-版本研究"),
    ("v0.8.0", os.path.join(TP, "vllm-versions", "v0.8.0"), "vllm", "P2-版本研究"),
    ("v0.10.0", os.path.join(TP, "vllm-versions", "v0.10.0"), "vllm", "P2-版本研究"),
    ("v0.30.0", os.path.join(TP, "vllm-v0.30.0"), "vllm", "P2-版本研究"),
    ("sglang-v0.5.20", os.path.join(TP, "sglang-v0.5.20"), "python/sglang", "P3-sglang"),
]


def main():
    for label, root, pkg, outdir in JOBS:
        pkg_path = os.path.join(root, pkg)
        if not os.path.isdir(pkg_path):
            print(f"SKIP {label}: 目录不存在 {pkg_path}")
            continue
        out_base = os.path.join(REC, outdir)
        os.makedirs(out_base, exist_ok=True)
        params_out = os.path.join(out_base, f"{label}-params.json")
        cands_out = os.path.join(out_base, f"{label}-candidates.json")
        r1 = subprocess.run([PY, os.path.join(SCRIPTS, "extract_params.py"), root, params_out, pkg, label],
                            capture_output=True, text=True)
        print(f"[{label}] params: {r1.stdout.strip().splitlines()[-1] if r1.stdout.strip() else r1.stderr[-200:]}")
        r2 = subprocess.run([PY, os.path.join(SCRIPTS, "scan_constraint_candidates.py"), root, cands_out, pkg, label],
                            capture_output=True, text=True)
        print(f"[{label}] candidates: {r2.stdout.strip().splitlines()[-1] if r2.stdout.strip() else r2.stderr[-200:]}")
    print("STATIC MATRIX DONE")


if __name__ == "__main__":
    main()
