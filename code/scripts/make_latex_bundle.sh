#!/usr/bin/env bash
set -e
LAT=/mnt/f/文献/AgentOps/论文/latex
OUT="$LAT/tse-latex-bundle.zip"
WORK=/tmp/tsebundle
rm -rf "$WORK"; mkdir -p "$WORK/figs"

# 主文件 + 图（保持 figs/ 结构）
cp "$LAT/main.tex" "$WORK/"
cp "$LAT"/figs/*.pdf "$WORK/figs/" 2>/dev/null || true
cp "$LAT"/figs/*.png "$WORK/figs/" 2>/dev/null || true

# IEEEtran 类文件（评审端可能缺）
CLS=$(find ~/texlive/2026/texmf-dist/tex/latex/ieeetran -name 'IEEEtran.cls' | head -1)
[ -n "$CLS" ] && cp "$CLS" "$WORK/" && echo "已含 IEEEtran.cls"

# 说明
cat > "$WORK/README-编译说明.txt" <<'EOF'
TSE 投稿 LaTeX 打包件
- 主文件：main.tex（IEEEtran journal 格式）
- 图形：figs/（PDF 矢量图；pdflatex 直接可用）
- 参考文献：在 main.tex 内以 \begin{thebibliography} 内联，无需 BibTeX
- 依赖：IEEEtran.cls（如果系统未安装，已随包提供）、graphicx、xcolor、amsmath、array、booktabs 等标准宏包
- 编译：pdflatex main.tex 连续两次
EOF

cd "$WORK" && zip -qr "$OUT" . && cd /
echo "== 打包完成 =="
ls -la "$OUT"
unzip -l "$OUT" | head -20
