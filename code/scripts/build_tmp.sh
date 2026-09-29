#!/usr/bin/env bash
set -e
LAT=/mnt/f/文献/AgentOps/论文/latex
TMP=/tmp/mainbuild
rm -rf "$TMP"; mkdir -p "$TMP"
cd "$LAT"
export TEXINPUTS="$LAT:"
~/texlive/2026/bin/x86_64-linux/pdflatex -interaction=nonstopmode -output-directory="$TMP" main.tex >/tmp/b1.log 2>&1 || true
~/texlive/2026/bin/x86_64-linux/pdflatex -interaction=nonstopmode -output-directory="$TMP" main.tex >/tmp/b2.log 2>&1 || true
echo "== 临时目录构建结果 =="
grep -c '^!' /tmp/b2.log || true
echo -n "undefined: "; grep -c 'undefined' /tmp/b2.log || true
echo -n "Overfull:  "; grep -c 'Overfull' /tmp/b2.log || true
grep -o 'Output written on .*main.pdf ([0-9]* pages' /tmp/b2.log | head -1
ls -la "$TMP/main.pdf"
