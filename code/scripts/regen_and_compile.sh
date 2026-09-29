#!/usr/bin/env bash
# 重新生成论文图并同步到 latex/figs，然后重编译
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"

echo "== 重生成 fig1-7（make_paper_figs.py） =="
python "/mnt/f/文献/AgentOps/代码/scripts/make_paper_figs.py" 2>&1 | tail -10

echo ""
echo "== 重生成 fig8-9（make_p4_figs.py） =="
python "/mnt/f/文献/AgentOps/代码/scripts/make_p4_figs.py" 2>&1 | tail -4

echo ""
echo "== 同步到 latex/figs =="
cp "/mnt/f/文献/AgentOps/论文/figs/"*.pdf "/mnt/f/文献/AgentOps/论文/latex/figs/"
ls "/mnt/f/文献/AgentOps/论文/latex/figs/" | head -12

echo ""
echo "== 重编译 =="
BIN="$HOME/texlive/2026/bin/x86_64-linux"
export PATH="$BIN:$PATH"
cd "/mnt/f/文献/AgentOps/论文/latex"
pdflatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1
pdflatex -interaction=nonstopmode -halt-on-error main.tex 2>&1 | tail -5
echo "Overfull: $(grep -ac Overfull main.log || true)"
grep -a "Output written" main.log | tail -1
