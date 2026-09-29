#!/usr/bin/env bash
# 用清华镜像装的 TeX Live 编译 TSE 稿件（跑两遍解析交叉引用）
set -uo pipefail
TEXDIR="$HOME/texlive/2026"
BIN="$TEXDIR/bin/x86_64-linux"
export PATH="$BIN:$PATH"
WORK="/mnt/f/文献/AgentOps/论文/latex"

if [ ! -x "$BIN/pdflatex" ]; then
  echo "!! pdflatex 不存在，TeX Live 尚未装好"
  exit 1
fi

echo "== 检查 IEEEtran.cls =="
if ! kpsewhich IEEEtran.cls > /dev/null 2>&1; then
  echo "缺失 → 经清华镜像补装 collection-publishers"
  "$BIN/tlmgr" install collection-publishers --repository \
    https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/tlnet || true
fi
kpsewhich IEEEtran.cls || echo "!! 仍无 IEEEtran"

cd "$WORK"
echo ""
echo "== 第 1 遍编译 =="
pdflatex -interaction=nonstopmode -halt-on-error main.tex 2>&1 | tail -12
echo ""
echo "== 第 2 遍编译（解析交叉引用） =="
pdflatex -interaction=nonstopmode -halt-on-error main.tex 2>&1 | tail -12
echo ""
echo "== 结果 =="
ls -la main.pdf 2>/dev/null && echo "✅ 编译成功" || echo "❌ 无 main.pdf"
echo ""
echo "== 警告/错误摘要 =="
grep -E "^(!|LaTeX Warning|Overfull|Underfull)" main.log 2>/dev/null | sort | uniq -c | sort -rn | head -15 || true
