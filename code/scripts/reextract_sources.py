# -*- coding: utf-8 -*-
"""用 Python 正确重解压 P2/P3 源码（修复 PowerShell 中文路径乱码问题）"""
import os
import tarfile

TP = r"F:\文献\AgentOps\代码\third_party"
TEMP = os.environ.get("TEMP") or r"C:\Users\Administrator\AppData\Local\Temp"

JOBS = [
    ("sglang-v0.5.20.tar.gz", os.path.join(TP, "sglang-v0.5.20")),
    ("vllm-v0.4.2.tar.gz", os.path.join(TP, "vllm-versions", "v0.4.2")),
    ("vllm-v0.5.5.tar.gz", os.path.join(TP, "vllm-versions", "v0.5.5")),
    ("vllm-v0.6.6.tar.gz", os.path.join(TP, "vllm-versions", "v0.6.6")),
    ("vllm-v0.8.0.tar.gz", os.path.join(TP, "vllm-versions", "v0.8.0")),
    ("vllm-v0.10.0.tar.gz", os.path.join(TP, "vllm-versions", "v0.10.0")),
]


def main():
    for name, dest in JOBS:
        src = os.path.join(TEMP, name)
        if not os.path.exists(src):
            print("MISSING tarball:", src)
            continue
        if os.path.isdir(dest) and os.listdir(dest):
            print("EXISTS, skip:", dest)
            continue
        os.makedirs(dest, exist_ok=True)
        n = 0
        with tarfile.open(src, "r:gz") as t:
            for m in t.getmembers():
                parts = m.name.split("/", 1)
                if len(parts) < 2 or not parts[1]:
                    continue
                m.name = parts[1]
                t.extract(m, dest)
                n += 1
        print(f"extracted: {name} -> {dest}  members={n}  top_entries={len(os.listdir(dest))}")
    print("RE-EXTRACT DONE")


if __name__ == "__main__":
    main()
