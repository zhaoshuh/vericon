# -*- coding: utf-8 -*-
"""R2 叙事同步：Paper1-draft-v2.md 过时文本修正 + scoot-drift.json 判词更新（2026-09-29）"""
import json

MD = "/mnt/f/文献/AgentOps/论文/Paper1-draft-v2.md"
JS = "/mnt/f/文献/AgentOps/实验记录/S4验证/scoot-drift.json"

pairs = [
    # 1) 摘要：去“可能一开始就错”，改为“随版本衰减”
    ("and, as we show empirically, **unreliable: it can be wrong from the start and it decays across engine versions**",
     "and, as we show empirically, **decays across engine versions**"),
    # 2) 摘要：SCOOT 三规则结论 → 衰减叙事
    ("We further show that **SCOOT's three hand-written rules do not survive scrutiny: one is not enforced by any version we checked (an over-assertion rather than a code constraint), one lost its practical force as engine defaults changed, and only one remains stable across five releases**",
     "We further show that **two of SCOOT's three hand-written rules no longer hold in current releases: one was a runtime guard in the anchor versions that upstream later removed, and one lost its practical force as engine defaults changed**"),
    # 3) 贡献 1
    ("SCOOT's three hand-written rules do not survive scrutiny: **one is not enforced by any version we checked** (chunked prefill and prefix caching coexist in all three execution-tested versions; source-level zero hits across six releases \u2014 an over-assertion rather than a code constraint), and **one lost its practical force** as engine defaults changed",
     "SCOOT's three hand-written rules do not all survive scrutiny: **one was a real runtime-enforced constraint in the anchor versions that upstream later removed** (v0.4.2/v0.5.5 raise at runtime when a prefix-cache hit occurs under chunked prefill, `worker/model_runner.py`; the guard is gone from v0.6.6 onward \u2014 construction-time checks never rejected the combination), and **one lost its practical force** as engine defaults changed"),
    # 4) §2.4 表：R2 行
    ("| chunked-prefill \u22a5 prefix-caching | **no mutual-exclusion check found** in v0.4.2/v0.5.5 (the only interaction is an auto-enable rule: chunked prefill is enabled when prefix caching is off, `engine/arg_utils.py:833\u2013838`); in v0.30.0 both flags coexist in a constructed `VllmConfig` | **not a code constraint (over-assertion)** |",
     "| chunked-prefill \u22a5 prefix-caching | **runtime guard** in v0.4.2 (`worker/model_runner.py:254\u2013258`) and v0.5.5 (`502\u2013504`): raises on a prefix-cache hit under chunked prefill; **removed from the main runner in v0.6.6+** after upstream added support | **enforced at the anchor versions; removed later (decay)** |"),
    # 5) FAQ 段
    ("Of SCOOT's three rules: **one is stable across five releases (execution-confirmed on v0.5.5, v0.10.0, and v0.30.0); one is not enforced by any version we checked \u2014 zero source-level hits and successful construction on all three execution-tested versions (it appears to be an over-assertion rather than a code constraint); one keeps identical semantics but lost practical force because V1 enables chunked prefill by default.**",
     "Of SCOOT's three rules: **one is stable across five releases** (execution-confirmed on v0.5.5, v0.10.0, and v0.30.0); **one was a runtime-enforced constraint in the anchor versions that upstream later removed** when it added support for the combination (v0.4.2/v0.5.5 `worker/model_runner.py` raises on a prefix-cache hit under chunked prefill; the guard is absent from the main runner in v0.6.6 onward \u2014 construction-path checks never rejected the combination, which is why our construction tests at v0.5.5/v0.10.0/v0.30.0 all pass); **one keeps identical semantics but lost practical force** because V1 enables chunked prefill by default."),
    # 6) FAQ 收尾句
    ("**Hand-written constraint sets are unreliable \u2014 they can be wrong from the start and they decay; automatic extraction with execution verification is necessary.**",
     "**Hand-written constraint sets decay; and runtime guards sit outside construction-path verification \u2014 automatic extraction with execution verification is necessary.**"),
    # 7) S 臂 invalid 率 10% → 9.5%
    ("(invalid rate 10%)", "(9.5% invalid)"),
    # 8) 相关工作：unreliable → decayed
    ("because two of SCOOT's three published rules are unreliable (\u00a72.3)",
     "because two of SCOOT's three published rules have since decayed (\u00a72.3)"),
    # 9) §2.4 引言补一句（运行时守卫复核方法）
    ("We constructed violating configurations for SCOOT's three vLLM rules and ran vLLM v0.30.0's validation path:",
     "We constructed violating configurations for SCOOT's three vLLM rules and ran vLLM v0.30.0's validation path; because rule #2 turned out to be a *runtime* guard, we additionally re-checked it at source level across versions (a construction-only protocol cannot observe runtime guards):"),
]

text = open(MD, encoding="utf-8").read()
report = []
for i, (old, new) in enumerate(pairs, 1):
    c = text.count(old)
    report.append(f"[{i}] count={c}")
    if c >= 1:
        text = text.replace(old, new)
open(MD, "w", encoding="utf-8", newline="").write(text)

# JSON 更新
j = json.load(open(JS, encoding="utf-8"))
j["verdict"]["SCOOT#2"] = ("v0.30.0 构造测试中不拒绝（两特性可共存）；但注意：v0.4.2/v0.5.5 曾有运行期守卫，属衰减而非从未成立"
                           "（见 correction_2026_09_29）")
j["refinement_2026_09_27"]["R2"] = ("【已更正，见 correction_2026_09_29】原判词（过多依赖配置名 token 搜索）不成立：R2 是运行期守卫，"
                                     "v0.4.2/v0.5.5 在 prefix-cache 命中 + chunked prefill 时抛 RuntimeError；v0.6.6+ 被上游移除。")
j["refinement_2026_09_27"]["verdict_refined"]["SCOOT#2"] = ("更正（2026-09-29）：锚定版本中是运行时守卫（v0.4.2 :254-258 / v0.5.5 :502-504），"
                                                            "v0.6.6+ 移除 \u2192 属\u201c约束随版本衰减\u201d，而非\u201c从未成立\u201d；构造式验证无法观察运行期守卫。")
j["correction_2026_09_29"] = {
    "trigger": "TSE 审稿模拟（配置分析方向）复核 + 本地源码复核：原 token 搜索漏检（守卫触发用运行期变量 prefix_cache_hit，消息中无配置字段名）",
    "R2_corrected": ("v0.4.2 worker/model_runner.py:254-258 \u2014 RuntimeError(\"chunked prefill cannot be used with prefix caching now.\")；"
                     "v0.5.5 :502-504 同款；触发条件为运行期 prefix-cache 命中（非配置期可构造）"),
    "v0_6_6_plus": "主 runner 已无此守卫（上游加入两特性共存支持）",
    "narrative": "正确叙事：R2 = 衰减（运行时守卫被移除），非\u201c过度断言/从未成立\u201d；同时说明构造式执行验证的边界\u2014\u2014构造路径看不到运行期守卫。",
    "affected_artifacts": ["论文/latex/main.tex（已同步）", "论文/Paper1-draft-v2.md（已同步）", "实验记录/P2-版本研究/SCOOT规则深查.md（已同步）"],
}
json.dump(j, open(JS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("\n".join(report))
print("JSON updated ok")
