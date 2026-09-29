#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf, re
PDF = "/mnt/f/文献/AgentOps/论文/latex/main.pdf"
doc = pymupdf.open(PDF)
p = doc[0]
print("== PDF 预检 ==")
print("页数:", len(doc))
print("页面尺寸(pt):", round(p.rect.width,1), "x", round(p.rect.height,1), "(Letter=612x792, A4=595x842)")
import os
print("文件大小(KB):", round(os.path.getsize(PDF)/1024,1))
fonts = set()
for pg in doc:
    for f in pg.get_fonts():
        fonts.add((f[3], f[4]))  # basefont, ext
notemb = [f for f in fonts if f[1] == ""]
print("字体数:", len(fonts), "| 未嵌入:", notemb if notemb else "无（全部嵌入）")
print("链接注解总数:", sum(len(pg.get_links()) for pg in doc))
print("元数据:", {k: doc.metadata.get(k) for k in ("title","author","subject","creator","producer")})
txt = doc[0].get_text()
print("首页含作者名:", "Shuheng Zhao" in txt, "| 含邮箱:", "zshbdfdc" in txt)
PYEOF
echo ""
echo "== TeX 头部（标题/摘要/关键词） =="
sed -n '30,50p' /mnt/f/文献/AgentOps/论文/latex/main.tex | cut -c1-160
echo ""
echo "== 关键词行 =="
grep -n 'IEEEkeywords\|index terms\|Index Terms' /mnt/f/文献/AgentOps/论文/latex/main.tex | head -3
echo ""
echo "== Cover letter 全文 =="
cat /mnt/f/文献/AgentOps/论文/latex/cover-letter.txt
