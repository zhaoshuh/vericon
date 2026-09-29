# -*- coding: utf-8 -*-
"""极简 CDP 客户端（Windows 侧运行）：驱动本机 Chrome 完成网页操作
用法：
  python cdp.py targets                     列出页面目标
  python cdp.py nav <url>                   当前标签导航
  python cdp.py eval "<js>"                 执行 JS（返回 JSON）
  python cdp.py text <css> <value>          向输入框写值（React 兼容）
  python cdp.py click <css>                 点击元素
  python cdp.py upload <css> <abs_path>     把文件塞进 <input type=file>
  python cdp.py wait <css> [secs]           等待元素出现
"""
import json
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import websocket  # websocket-client

PORT = 9222


def targets():
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=5) as r:
        return json.load(r)


def page_ws():
    for t in targets():
        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
            return t["webSocketDebuggerUrl"], t.get("url", "")
    raise SystemExit("no page target")


class CDP:
    def __init__(self):
        url, self.url = page_ws()
        self.ws = websocket.create_connection(url, timeout=30, suppress_origin=True)
        self.i = 0

    def call(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.i:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def js(self, expr, by_value=True):
        r = self.call("Runtime.evaluate", expression=expr, returnByValue=by_value, awaitPromise=True)
        out = r.get("result", {})
        if by_value:
            return out.get("value")
        return out

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass

    def send_raw(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        return self.i

    def wait_event(self, event, timeout=10):
        t0 = time.time()
        self.ws.settimeout(1.0)
        while time.time() - t0 < timeout:
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                continue
            if msg.get("method") == event:
                return msg.get("params")
        return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    c = CDP()
    try:
        if cmd == "targets":
            for t in targets():
                print(t.get("type"), "|", (t.get("url") or "")[:110], "|", (t.get("title") or "")[:60])
        elif cmd == "front":
            c.call("Page.enable")
            c.call("Page.bringToFront")
            print("front ok")
        elif cmd == "shot":
            import base64
            out = sys.argv[2] if len(sys.argv) > 2 else "shot.png"
            c.call("Page.enable")
            r = c.call("Page.captureScreenshot", format="png", captureBeyondViewport=False)
            data = base64.b64decode(r["data"])
            with open(out, "wb") as f:
                f.write(data)
            print("shot ->", out, len(data) // 1024, "KB")
        elif cmd == "upn":
            n, path = int(sys.argv[2]), sys.argv[3]
            c.call("DOM.enable")
            obj = c.js("document.querySelectorAll('input[type=file]')[%d]" % n, by_value=False)
            oid = obj.get("objectId")
            if not oid:
                print("NOT_FOUND")
                return
            c.call("DOM.setFileInputFiles", files=[path], objectId=oid)
            cnt = c.js("(() => { const el = document.querySelectorAll('input[type=file]')[%d];"
                       " el.dispatchEvent(new Event('input',{bubbles:true}));"
                       " el.dispatchEvent(new Event('change',{bubbles:true}));"
                       " return el.files.length; })()" % n)
            print("UPLOADED idx", n, path, "| files on input:", cnt)
        elif cmd == "dl":
            expr, outdir = sys.argv[2], sys.argv[3]
            c.call("Browser.setDownloadBehavior", behavior="allow", downloadPath=outdir, eventsEnabled=True)
            c.js("(() => { const a = (%s); if (!a) return 'NF'; a.click(); return 'CLICKED'; })()" % expr)
            time.sleep(12)
            print("download requested ->", outdir)
        elif cmd == "type":
            text = sys.argv[2]
            c.call("Input.insertText", text=text)
            print("TYPED:", text[:40])
        elif cmd == "key":
            k = sys.argv[2]
            keymap = {"Enter": ("Enter", 13), "Down": ("ArrowDown", 40), "Up": ("ArrowUp", 38),
                      "Esc": ("Escape", 27), "Tab": ("Tab", 9)}
            key, code = keymap.get(k, (k, 0))
            for t in ("keyDown", "keyUp"):
                c.call("Input.dispatchKeyEvent", type=t, key=key, windowsVirtualKeyCode=code, nativeVirtualKeyCode=code)
            print("KEY:", k)
        elif cmd == "drop":
            expr = sys.argv[2]
            path = sys.argv[3]
            c.call("Page.enable")
            rect = c.js("(() => { const el = (%s); if (!el) return null; el.scrollIntoView({block:'center'});"
                        " const r = el.getBoundingClientRect(); return {x: r.left + r.width/2, y: r.top + r.height/2, t: (el.innerText||'').trim().slice(0,40)}; })()" % expr)
            if not rect:
                print("ELEMENT_NOT_FOUND")
                return
            x, y = rect["x"], rect["y"]
            data = {"items": [], "files": [path], "dragOperationsMask": 1}
            for t in ("dragEnter", "dragOver", "drop"):
                c.call("Input.dispatchDragEvent", type=t, x=x, y=y, data=data)
            print("DROPPED", path, "at", round(x), round(y), "|", rect.get("t", ""))
        elif cmd == "iclick":
            expr = sys.argv[2]
            path = sys.argv[3] if len(sys.argv) > 3 else None
            c.call("Page.enable")
            c.call("DOM.enable")
            c.call("Page.setInterceptFileChooserDialog", enabled=True)
            rect = c.js("(() => { const el = (%s); if (!el) return null; el.scrollIntoView({block:'center'});"
                        " const r = el.getBoundingClientRect(); return {x: r.left + r.width/2, y: r.top + r.height/2, t: (el.innerText||'').trim()}; })()" % expr)
            if not rect:
                print("ELEMENT_NOT_FOUND")
                return
            x, y = rect["x"], rect["y"]
            c.call("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
            c.call("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", clickCount=1)
            c.call("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left", clickCount=1)
            print("CLICKED at", round(x), round(y), "|", rect.get("t", "")[:30])
            ev = c.wait_event("Page.fileChooserOpened", timeout=10)
            if not ev:
                print("NO_CHOOSER")
                return
            if path:
                c.call("DOM.setFileInputFiles", files=[path], backendNodeId=ev.get("backendNodeId"))
                print("ADDED", path)
            else:
                print("CHOOSER_OPENED", ev.get("mode"))
        elif cmd == "addfile3":
            expr, path = sys.argv[2], sys.argv[3]
            c.call("Page.enable")
            c.call("DOM.enable")
            c.call("Page.setInterceptFileChooserDialog", enabled=True)
            click_js = "(() => { const el = (%s); if (!el) return 'NOT_FOUND'; el.click(); return 'CLICKED'; })()" % expr
            c.send_raw("Runtime.evaluate", expression=click_js, userGesture=True)
            ev = c.wait_event("Page.fileChooserOpened", timeout=10)
            if not ev:
                print("NO_CHOOSER")
                return
            c.call("DOM.setFileInputFiles", files=[path], backendNodeId=ev.get("backendNodeId"))
            print("ADDED", path, "| backendNodeId", ev.get("backendNodeId"))
        elif cmd == "addfile":
            section, path = sys.argv[2], sys.argv[3]
            c.call("Page.enable")
            c.call("DOM.enable")
            c.call("Page.setInterceptFileChooserDialog", enabled=True)
            js = """(() => {
              const norm = s => (s||'').replace(/\\s+/g,' ').trim();
              const h = [...document.querySelectorAll('*')].filter(e => norm(e.innerText) === %s)[0];
              if (!h) return 'SECTION_NOT_FOUND';
              let p = h;
              for (let k = 0; k < 7 && p; k++) {
                p = p.parentElement; if (!p) break;
                const b = [...p.querySelectorAll('button')].find(x => /Add Files|Upload|Choose/i.test(norm(x.innerText)));
                if (b) { b.click(); return 'CLICKED: ' + norm(b.innerText); }
              }
              return 'BTN_NOT_FOUND';
            })()""" % json.dumps(section)
            c.send_raw("Runtime.evaluate", expression=js)
            ev = c.wait_event("Page.fileChooserOpened", timeout=10)
            if not ev:
                print("NO_FILE_CHOOSER (button click failed or dialog not intercepted)")
                return
            c.call("DOM.setFileInputFiles", files=[path], backendNodeId=ev.get("backendNodeId"))
            print("ADDED", path, "->", section, "| backendNodeId", ev.get("backendNodeId"))
        elif cmd == "tclick":
            txt = sys.argv[2]
            js = """(() => {
              const norm = s => (s||'').replace(/\\s+/g,' ').trim();
              const els = Array.from(document.querySelectorAll('a,button,input[type=submit],li,span,div'));
              const el = els.filter(e => norm(e.innerText) === %s && e.offsetParent !== null)
                             .sort((a,b) => a.innerText.length - b.innerText.length)[0];
              if (!el) return 'NOT_FOUND';
              el.click();
              return 'CLICKED: ' + norm(el.innerText).slice(0,50);
            })()""" % json.dumps(txt)
            print(c.js(js))
        elif cmd == "nav":
            c.call("Page.enable")
            c.call("Page.navigate", url=sys.argv[2])
            time.sleep(2)
            print("nav ->", sys.argv[2])
        elif cmd == "eval":
            v = c.js(sys.argv[2])
            print(json.dumps(v, ensure_ascii=False)[:4000])
        elif cmd == "text":
            sel, val = sys.argv[2], sys.argv[3]
            js = """(() => {
              const el = document.querySelector(%s);
              if (!el) return 'NOT_FOUND';
              const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
              const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
              setter.call(el, %s);
              el.dispatchEvent(new Event('input', {bubbles: true}));
              el.dispatchEvent(new Event('change', {bubbles: true}));
              return 'OK len=' + el.value.length;
            })()""" % (json.dumps(sel), json.dumps(val))
            print(c.js(js))
        elif cmd == "click":
            sel = sys.argv[2]
            js = """(() => { const els = Array.from(document.querySelectorAll(%s));
                     const el = els.find(e => e.offsetParent !== null) || els[0];
                     if (!el) return 'NOT_FOUND'; el.click(); return 'CLICKED ' + (el.innerText||'').slice(0,40); })()""" % json.dumps(sel)
            print(c.js(js))
        elif cmd == "upload":
            sel, path = sys.argv[2], sys.argv[3]
            c.call("DOM.enable")
            obj = c.js("document.querySelector(%s)" % json.dumps(sel), by_value=False)
            oid = obj.get("objectId")
            if not oid:
                print("NOT_FOUND")
                return
            c.call("DOM.setFileInputFiles", files=[path], objectId=oid)
            print("UPLOADED", path)
        elif cmd == "wait":
            sel = sys.argv[2]
            secs = float(sys.argv[3]) if len(sys.argv) > 3 else 20
            t0 = time.time()
            while time.time() - t0 < secs:
                if c.js("!!document.querySelector(%s)" % json.dumps(sel)):
                    print("FOUND", sel)
                    return
                time.sleep(1)
            print("TIMEOUT", sel)
        else:
            print("unknown cmd", cmd)
    finally:
        c.close()


if __name__ == "__main__":
    main()
