#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import pymupdf
LAT = "/mnt/f/文献/AgentOps/论文/latex/main.pdf"
doc = pymupdf.open(LAT)
print("pages:", len(doc))
for i, page in enumerate(doc):
    hits = []
    for kw in ("Constraint type distribution", "Figure 2.", "Figure 1.", "Figure 3.",
               "Extracted constraint types"):
        if page.search_for(kw):
            hits.append(kw)
    imgs = page.get_images()
    txt_rects = [b[:4] for b in page.get_text("blocks") if b[6] == 0]
    img_rects = []
    for im in page.get_images(full=True):
        rects = page.get_image_rects(im[0])
        img_rects += rects
    overlaps = 0
    for ir in img_rects:
        for tr in txt_rects:
            if pymupdf.Rect(ir).intersects(pymupdf.Rect(tr)):
                overlaps += 1
    # 页面底部溢出文本
    ph = page.rect.height
    low = [tr for tr in txt_rects if tr[3] > ph - 40]
    if hits or overlaps or len(low) > 2:
        print(f"p{i+1}: hits={hits} imgs={len(img_rects)} img-txt-overlaps={overlaps} low_blocks={len(low)}")
PYEOF
