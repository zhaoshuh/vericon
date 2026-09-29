# -*- coding: utf-8 -*-
"""把 cover-letter.txt 转成 cover-letter.pdf（ScholarOne 一般不收 .txt）"""
import os
import subprocess

LAT = "/mnt/f/文献/AgentOps/论文/latex"
src = open(f"{LAT}/cover-letter.txt", encoding="utf-8").read()

# LaTeX 转义
esc = (src.replace("\\", r"\textbackslash{}")
          .replace("&", r"\&").replace("%", r"\%").replace("$", r"\$")
          .replace("#", r"\#").replace("_", r"\_")
          .replace("{", r"\{").replace("}", r"\}")
          .replace("~", r"\textasciitilde{}").replace("^", r"\textasciicircum{}"))

tex = ("\\documentclass[11pt]{article}\n"
       "\\usepackage[margin=1in]{geometry}\n"
       "\\usepackage[T1]{fontenc}\n"
       "\\usepackage{lmodern}\n"
       "\\setlength{\\parskip}{6pt}\n"
       "\\begin{document}\n"
       "\\thispagestyle{empty}\n"
       + esc +
       "\n\\end{document}\n")
open(f"{LAT}/cover-letter.tex", "w", encoding="utf-8", newline="").write(tex)

r = subprocess.run([os.path.expanduser("~/texlive/2026/bin/x86_64-linux/pdflatex"),
                    "-interaction=nonstopmode", "-halt-on-error", "cover-letter.tex"],
                   cwd=LAT, capture_output=True, text=True)
print("pdflatex rc =", r.returncode)
if r.returncode != 0:
    print((r.stdout or "")[-800:])
import fitz
try:
    d = fitz.open(f"{LAT}/cover-letter.pdf")
    print("cover-letter.pdf 页数:", len(d))
    print("首行:", d[0].get_text().splitlines()[0] if d[0].get_text() else "")
except Exception as e:
    print("PDF 检查失败:", e)
