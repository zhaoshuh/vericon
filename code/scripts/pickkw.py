# -*- coding: utf-8 -*-
"""按 ACM 分类标题选择一个关键词（走 CDP），并回报已选数量
用法: python pickkw.py "<搜索词>" "<精确标题>"
"""
import json
import re
import sys
import time

sys.path.insert(0, r"F:\文献\AgentOps\代码\scripts")
from cdp import CDP  # noqa: E402


def selected_count(c):
    t = c.js("document.body.innerText") or ""
    m = re.search(r"(\d+)\s+selected keywords", t)
    return m.group(1) if m else "?"


def main():
    term, title = sys.argv[1], sys.argv[2]
    c = CDP()
    try:
        c.call("Page.enable")
        c.js("(() => { const i=document.querySelector('input.textFormControl-element');"
             " const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;"
             " s.call(i,''); i.dispatchEvent(new Event('input',{bubbles:true})); i.focus(); return 1; })()")
        c.call("Input.insertText", text=term)
        time.sleep(2.5)
        rect = c.js("(() => { const t=[...document.querySelectorAll('.treeSelectorItem-title')]"
                    ".find(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()===%s); if(!t) return null;"
                    " const ck=t.querySelector('input[type=checkbox]'); if(!ck) return null;"
                    " ck.scrollIntoView({block:'center'}); const r=ck.getBoundingClientRect();"
                    " return {x:r.left+r.width/2, y:r.top+r.height/2, checked:ck.checked}; })()" % json.dumps(title))
        if not rect:
            print("TITLE_NOT_FOUND |", title, "| selected:", selected_count(c))
            return
        if not rect["checked"]:
            for t in ("mouseMoved", "mousePressed", "mouseReleased"):
                c.call("Input.dispatchMouseEvent", type=t, x=rect["x"], y=rect["y"],
                       button="left", clickCount=1)
            time.sleep(1.2)
        print("OK |", title, "| selected:", selected_count(c))
    finally:
        c.close()


if __name__ == "__main__":
    main()
