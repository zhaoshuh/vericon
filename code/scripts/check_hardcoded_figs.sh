#!/usr/bin/env bash
T=/mnt/f/文献/AgentOps/论文/latex/main.tex
echo "=== 硬编码图号引用 ==="
grep -n 'Figures\? [0-9]\|Figure~[0-9]\|Fig\. [0-9]' "$T" | grep -v '\\ref' | head -10
echo "=== §II-D 区域 (122-152) ==="
sed -n '122,152p' "$T"
