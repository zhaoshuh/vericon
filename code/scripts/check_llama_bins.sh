#!/usr/bin/env bash
BIN_DIR="/mnt/f/文献/AgentOps/代码/third_party/llama-bin-v0.5.0"
echo "== 二进制目录 =="
ls -la "$BIN_DIR" 2>/dev/null | head -20
echo ""
echo "== llama-bench 可用性 =="
LB=$(find "$BIN_DIR" -name "llama-bench" -type f 2>/dev/null | head -1)
echo "llama-bench: $LB"
echo ""
echo "== 模型文件 =="
find /mnt/f/文献/AgentOps/代码/third_party/models -name "*.gguf" 2>/dev/null | head -5
echo ""
echo "== libgomp 路径（S6 记录用） =="
find "$BIN_DIR" -name "libgomp*" 2>/dev/null | head -3
find /mnt/f/文献/AgentOps/代码 -name "libgomp*" 2>/dev/null | head -3
