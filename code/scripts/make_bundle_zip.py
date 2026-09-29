# -*- coding: utf-8 -*-
"""用 zipfile 打包 LaTeX 投稿包"""
import os
import shutil
import zipfile

LAT = "/mnt/f/文献/AgentOps/论文/latex"
WORK = "/tmp/tsebundle"
OUT = f"{LAT}/tse-latex-bundle.zip"

shutil.rmtree(WORK, ignore_errors=True)
os.makedirs(f"{WORK}/figs", exist_ok=True)
shutil.copy2(f"{LAT}/main.tex", f"{WORK}/main.tex")

n_fig = 0
for d, exts in ((f"{LAT}/figs", (".pdf", ".png")),):
    for fn in sorted(os.listdir(d)):
        if fn.lower().endswith(exts):
            shutil.copy2(os.path.join(d, fn), f"{WORK}/figs/{fn}")
            n_fig += 1

cls_src = None
for root, _, files in os.walk(os.path.expanduser("~/texlive/2026/texmf-dist/tex/latex/ieeetran")):
    if "IEEEtran.cls" in files:
        cls_src = os.path.join(root, "IEEEtran.cls")
        break
if cls_src:
    shutil.copy2(cls_src, f"{WORK}/IEEEtran.cls")

with open(f"{WORK}/README-编译说明.txt", "w", encoding="utf-8") as f:
    f.write("TSE 投稿 LaTeX 打包件\n"
            "- 主文件：main.tex（IEEEtran journal 格式）\n"
            "- 图形：figs/（PDF 矢量图，pdflatex 直接可用）\n"
            "- 参考文献：main.tex 内联 thebibliography（无需 BibTeX）\n"
            "- 依赖：IEEEtran.cls（随包提供）+ graphicx/xcolor/amsmath/array/booktabs 等标准宏包\n"
            "- 编译：pdflatex main.tex 两次\n")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(WORK):
        for fn in files:
            p = os.path.join(root, fn)
            z.write(p, os.path.relpath(p, WORK))

print("zip 已生成:", OUT, round(os.path.getsize(OUT) / 1024, 1), "KB")
with zipfile.ZipFile(OUT) as z:
    for n in z.namelist()[:16]:
        print("  ", n)
    print("   ... 共", len(z.namelist()), "个文件（图", n_fig, "个）")
