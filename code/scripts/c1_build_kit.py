# -*- coding: utf-8 -*-
"""C1 · 人类盲标套件构建（150 站点：两批金标准样本各 75，分层抽）
产出：实验记录/C1-人类盲标/
  - 标注工具.html（离线单文件；进度保存；导出 CSV）
  - sites-pack.json（站点+上下文，供核对）
"""
import html
import json
import os
import random

SRC = "/mnt/f/文献/AgentOps/代码/third_party/vllm-v0.30.0"
OUT = "/mnt/f/文献/AgentOps/实验记录/C1-人类盲标"
os.makedirs(OUT, exist_ok=True)

s1 = json.load(open("/mnt/f/文献/AgentOps/实验记录/P1b-金标准样本.json", encoding="utf-8"))["sites"]
s2 = json.load(open("/mnt/f/文献/AgentOps/实验记录/P1b-金标准样本2.json", encoding="utf-8"))["sites"]

def stratified_pick(sites, n, seed):
    rng = random.Random(seed)
    by_t = {}
    for s in sites:
        by_t.setdefault(s.get("tier", 3), []).append(s)
    quota = {t: max(1, round(n * len(v) / len(sites))) for t, v in by_t.items()}
    picked = []
    for t, v in sorted(by_t.items()):
        picked += rng.sample(v, min(quota[t], len(v)))
    rng.shuffle(picked)
    return picked[:n]

pick = stratified_pick(s1, 75, 777) + stratified_pick(s2, 75, 888)
print("抽中:", len(pick), "tier 分布:", {t: sum(1 for s in pick if s.get('tier') == t) for t in (1, 2, 3)})

items = []
for i, s in enumerate(pick):
    fp = os.path.join(SRC, s["file"])
    ctx = []
    try:
        lines = open(fp, encoding="utf-8", errors="replace").read().splitlines()
        lo, hi = max(0, s["line"] - 13), min(len(lines), s["line"] + 12)
        for ln in range(lo, hi):
            ctx.append([ln + 1, lines[ln][:220]])
    except Exception as e:
        ctx.append([0, f"(上下文读取失败: {e})"])
    items.append({
        "id": f"H{i+1:03d}", "src_batch": 1 if i < 75 else 2, "tier": s.get("tier"),
        "file": s["file"], "line": s["line"], "kind": s.get("kind", ""),
        "condition": (s.get("condition") or "")[:400], "exception": s.get("exception") or "",
        "message": (s.get("message") or "")[:300],
        "context": ctx, "site_line": s["line"],
    })

json.dump({"n": len(items), "source": "P1b 两批金标准样本（各 75，分层）", "items": items},
          open(os.path.join(OUT, "sites-pack.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 示例（已裁定，作为说明用） ----------
examples = [
    {"verdict": "YES", "file": "vllm/config/offload.py:102", "kind": "raise",
     "code": "raise ValueError('offload_group_size / offload_num_in_group / offload_prefetch_step must be consistent')",
     "why": "检查项由用户设置的分组卸载参数组合触发；属于配置约束。"},
    {"verdict": "NO", "file": "vllm/model_executor/layers/quantization/utils/marlin_utils_fp8.py:128", "kind": "assert",
     "code": "assert layer.weight.shape == (part_size_n, part_size_k)",
     "why": "张量形状内核自检；用户无论如何配置合法参数都不会因这条而失败。"},
    {"verdict": "NO", "file": "vllm/model_executor/models/adapters.py:377", "kind": "assert",
     "code": "assert pooler_config is not None",
     "why": "运行期接线检查（对象是否存在），不是参数组合规则。"},
    {"verdict": "NO", "file": "vllm/model_executor/layers/fused_moe/config.py:586", "kind": "assert",
     "code": "assert quant_config.per_act_token_quant == per_act_token_quant",
     "why": "内部一致性自检（同一设置的两个来源互查），非用户可触发的配置组合。"},
    {"verdict": "YES", "file": "vllm/v1/attention/backends/mla/flashmla_sparse.py:709", "kind": "assert",
     "code": "assert kv_cache_dtype in QUANTIZED_DS_MLA_CACHE_FORMATS",
     "why": "后端 × kv_cache_dtype 的组合约束：用户选择该后端 + 非法 dtype 即触发。"},
]

HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>配置约束站点盲标</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--acc:#2563eb;--ok:#16a34a;--no:#dc2626;--un:#ca8a04}
*{box-sizing:border-box}body{font-family:ui-sans-serif,'Segoe UI',system-ui;margin:0;background:var(--bg);color:#111}
header{position:sticky;top:0;background:#fff;border-bottom:1px solid #e5e7eb;padding:10px 18px;display:flex;align-items:center;gap:14px;z-index:9}
h1{font-size:16px;margin:0}.prog{flex:1;height:10px;background:#e5e7eb;border-radius:6px;overflow:hidden}
.prog>i{display:block;height:100%;width:0;background:var(--acc);transition:.2s}
main{max-width:920px;margin:20px auto;padding:0 16px 120px}
.card{background:var(--card);border:1px solid #e5e7eb;border-radius:12px;padding:18px;margin-bottom:16px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.meta{font-size:12.5px;color:#555;display:flex;flex-wrap:wrap;gap:10px;margin-bottom:8px}
.badge{background:#eef2ff;color:#3730a3;border-radius:6px;padding:1px 8px;font-weight:600}
pre.code{background:#0f172a;color:#e2e8f0;border-radius:8px;padding:12px;overflow:auto;font-size:12.5px;line-height:1.45;max-height:340px}
pre.code .hl{background:#334155;display:inline-block;width:100%}
.stmt{background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:8px 10px;font-size:13px;margin:8px 0;white-space:pre-wrap;word-break:break-word}
.btns{display:flex;gap:10px;margin-top:10px;flex-wrap:wrap}
button{border:0;border-radius:8px;padding:9px 16px;font-size:14px;font-weight:600;cursor:pointer}
.yes{background:#dcfce7;color:#166534}.yes.sel{background:var(--ok);color:#fff}
.no{background:#fee2e2;color:#991b1b}.no.sel{background:var(--no);color:#fff}
.un{background:#fef9c3;color:#854d0e}.un.sel{background:var(--un);color:#fff}
textarea{width:100%;margin-top:8px;border:1px solid #d1d5db;border-radius:8px;padding:8px;font-size:13px;resize:vertical;min-height:38px}
.foot{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #e5e7eb;padding:10px 18px;display:flex;gap:12px;align-items:center}
.export{background:var(--acc);color:#fff}
.note{font-size:13px;color:#444;line-height:1.6}
details{margin-top:6px}summary{cursor:pointer;font-weight:600;font-size:14px}
</style></head><body>
<header><h1>配置约束站点盲标（共 NNN 项）</h1><div class="prog"><i id="pi"></i></div><span id="pc" style="font-size:13px;color:#555">0/NNN</span></header>
<main>
 <div class="card"><details><summary>任务说明与判定标准（点开）</summary>
  <div class="note">
  <p><b>目标：</b>对下面每个源码站点（<code>assert</code> 或 <code>raise</code>），判断它是否为一条<b>配置约束</b>——即：<b>用户通过配置参数组合（命令行/配置字段/装载选项）就能触发的“拒绝非法配置”检查</b>。</p>
  <p><b>YES：</b>检查条件/消息涉及 ≥1 个配置参数，且失败的根源在用户的配置选择（含跨参数组合、平台/后端×参数组合）。<br>
     <b>NO：</b>内核/张量形状自检、检查点文件内容校验、运行期接线（<code>X is not None</code>、对象存在性）、环境探测（GPU/ray/文件系统）、请求级输入格式错误、内部一致性自检（同一设置的多个来源互查）。<br>
     <b>UNSURE：</b>上下文不足、边界情形——如实选它即可，不要勉强。</p>
  <p><b>示例（已裁定）：</b></p>
  EXAMPLEHTML
  <p>判定时<b>只看源码上下文本身</b>；不确定时选择 UNSURE 并在备注里写下疑问。</p>
  </div></details></div>
 <div id="list"></div>
</main>
<div class="foot"><span id="stat" style="font-size:13px;color:#555"></span><span style="flex:1"></span>
 <button class="un" onclick="jumpUnlabeled()">跳到未标项</button>
 <button class="export" onclick="exportCSV()">导出结果 CSV</button></div>
<script>
const DATA = ITEMJSON;
const EXAMPLE = null;
const KEY = 'c1_label_v1';
let state = JSON.parse(localStorage.getItem(KEY) || '{}');
function setV(id, v){ state[id] = state[id] || {}; state[id].v = v; save(); render(); }
function setN(id, n){ state[id] = state[id] || {}; state[id].n = n; save(); }
function save(){ localStorage.setItem(KEY, JSON.stringify(state)); }
function statText(){ const y=Object.values(state).filter(s=>s.v==='Y').length, n=Object.values(state).filter(s=>s.v==='N').length, u=Object.values(state).filter(s=>s.v==='U').length; document.getElementById('stat').textContent = `Y=${y} N=${n} U=${u} 未标=${DATA.length-y-n-u}`; const p=Math.round((y+n+u)/DATA.length*100); document.getElementById('pi').style.width=p+'%'; document.getElementById('pc').textContent=(y+n+u)+'/'+DATA.length; }
function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
function render(){
  const L = document.getElementById('list'); L.innerHTML='';
  DATA.forEach((it,i)=>{
    const st = state[it.id]||{};
    const div = document.createElement('div'); div.className='card'; div.id='card-'+it.id;
    let code = it.context.map(([ln,txt])=> `<span class="${ln===it.site_line?'hl':''}">${String(ln).padStart(5)} | ${esc(txt)}</span>`).join('\\n');
    div.innerHTML = `<div class="meta"><span class="badge">${i+1}/${DATA.length}</span><span>${it.id}</span><span>tier ${it.tier}</span><span>${esc(it.file)}:${it.line}</span><span>${esc(it.kind)}</span></div>
      <div class="stmt">${esc(it.kind)}: ${esc((it.condition||'').slice(0,300))}${it.message? '\\nmessage: '+esc(it.message.slice(0,200)):''}</div>
      <details><summary>源码上下文（±12 行）</summary><pre class="code">${code}</pre></details>
      <div class="btns">
        <button class="yes ${st.v==='Y'?'sel':''}" onclick="setV('${it.id}','Y')">是（YES）</button>
        <button class="no ${st.v==='N'?'sel':''}" onclick="setV('${it.id}','N')">否（NO）</button>
        <button class="un ${st.v==='U'?'sel':''}" onclick="setV('${it.id}','U')">不确定</button>
      </div>
      <textarea placeholder="备注（可选）" oninput="setN('${it.id}',this.value)">${esc(st.n||'')}</textarea>`;
    L.appendChild(div);
  });
  statText();
}
function jumpUnlabeled(){ for(const it of DATA){ const st=state[it.id]||{}; if(!st.v){ document.getElementById('card-'+it.id).scrollIntoView({behavior:'smooth'}); return; } } alert('全部已标注 ✅'); }
function exportCSV(){
  let rows = ['id,verdict,note,file,line,tier'];
  DATA.forEach(it=>{ const st=state[it.id]||{}; rows.push([it.id, st.v||'', '"'+(st.n||'').replace(/"/g,'""')+'"', it.file, it.line, it.tier].join(',')); });
  const blob = new Blob(['\\ufeff'+rows.join('\\n')], {type:'text/csv'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'c1_results.csv'; a.click();
}
render();
</script></body></html>"""

example_html = "\n".join(
    f'<p style="margin:6px 0"><b style="color:{"#16a34a" if e["verdict"]=="YES" else "#dc2626"}">{e["verdict"]}</b> '
    f'<code>{html.escape(e["file"])}</code><br><code>{html.escape(e["code"][:150])}</code><br><span style="color:#555">→ {html.escape(e["why"])}</span></p>'
    for e in examples)

page = (HTML.replace("NNN", str(len(items))).replace("ITEMJSON", json.dumps(items, ensure_ascii=False))
        .replace("EXAMPLEHTML", example_html))
open(os.path.join(OUT, "标注工具.html"), "w", encoding="utf-8").write(page)
print("HTML 大小(KB):", round(os.path.getsize(os.path.join(OUT, '标注工具.html')) / 1024, 1))
print("DONE ->", OUT)
