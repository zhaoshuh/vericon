#!/usr/bin/env bash
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
B=/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0/llama-b11194/llama-bench
M=~/models/qwen2.5-0.5b-instruct-q4_k_m.gguf
echo "== 1) ctk=q8_0 + fa=off（预期失败）=="
"$B" -m "$M" -t 4 -b 256 -ub 128 -fa off -ctk q8_0 -ctv f16 -p 256 -n 16 -r 1 > /tmp/ck1.txt 2>&1
echo "rc=$?"; tail -2 /tmp/ck1.txt | head -1
echo "== 2) ctk=q8_0 + fa=on（预期成功）=="
"$B" -m "$M" -t 4 -b 256 -ub 128 -fa on -ctk q8_0 -ctv f16 -p 256 -n 16 -r 1 > /tmp/ck2.txt 2>&1
echo "rc=$?"
echo "== 3) ctv=q8_0 + fa=off（对照，已知失败）=="
"$B" -m "$M" -t 4 -b 256 -ub 128 -fa off -ctk f16 -ctv q8_0 -p 256 -n 16 -r 1 > /tmp/ck3.txt 2>&1
echo "rc=$?"
echo "== 下载 1.5B 模型 =="
URL1="https://hf-mirror.com/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
URL2="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
cd ~/models
if [ -f qwen2.5-1.5b-instruct-q4_k_m.gguf ]; then
  echo "already exists"; ls -la qwen2.5-1.5b-instruct-q4_k_m.gguf
else
  echo "try hf-mirror..."
  timeout 600 curl -sL -o qwen2.5-1.5b-instruct-q4_k_m.gguf --retry 2 "$URL1" || true
  SZ=$(stat -c %s qwen2.5-1.5b-instruct-q4_k_m.gguf 2>/dev/null || echo 0)
  echo "size=$SZ"
  if [ "$SZ" -lt 500000000 ]; then
    echo "mirror failed/incomplete, try huggingface.co..."
    timeout 900 curl -sL -o qwen2.5-1.5b-instruct-q4_k_m.gguf --retry 2 "$URL2" || true
    SZ=$(stat -c %s qwen2.5-1.5b-instruct-q4_k_m.gguf 2>/dev/null || echo 0)
    echo "size2=$SZ"
  fi
  ls -la qwen2.5-1.5b-instruct-q4_k_m.gguf
fi
