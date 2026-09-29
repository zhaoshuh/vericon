# P2 · SCOOT 三条"已知约束"深查（源码级 + 执行级）

> 目的：把"人工约束会衰减"从轶事升级为**逐版本、逐规则的证据链**。
> 方法：① 源码级：多行窗口（±6 行）搜索 + 报错消息关键词；② 执行级（**三版本矩阵**）：v0.5.5（`v0.5.5-exec.json`）+ v0.10.0（`v0.10.0-exec.json`）+ v0.30.0（`scoot-drift.json`）。
> 版本：v0.4.2 / v0.5.5（SCOOT 原始锚点）、v0.30.0（当前）；SCOOT 原文：附录 A.2。

---

## R1 · `max_num_batched_tokens >= max_num_seqs`

| 版本 | 源码证据 | 结论 |
|---|---|---|
| v0.4.2 | `vllm/config.py:649`（校验行，同一模式） | ✅ 存在 |
| v0.5.5 | `vllm/config.py:938-942`：`if self.max_num_batched_tokens < self.max_num_seqs: raise ValueError("... must be greater than or equal to max_num_seqs ...")` | ✅ 存在（逐字同款） |
| **v0.5.5 执行级** | `SchedulerConfig(max_num_seqs=4096, max_num_batched_tokens=2048, max_model_len=2048)` → **`ValueError: max_num_batched_tokens (2048) must be greater than or equal to max_num_seqs (4096)`**；对照（mtib 4096 ≥ mns 128）构造成功 | ✅ **执行级确认** |
| **v0.10.0 执行级** | 同构用例 → **`ValidationError: max_num_batched_tokens (2048) must be greater than or equal to max_num_seqs (4096)`**（pydantic 化后仍强制）；对照通过（`v0.10.0-exec.json`） | ✅ **执行级确认** |
| v0.30.0 | `vllm/config/scheduler.py:309`；执行证伪通过（`max_num_batched_tokens (256) must be >= max_num_seqs (512)`） | ✅ 存在 |

**判定：跨 0.4.2→0.30.0 稳定存在**（5 个大版本跨度）。这是"少数没有衰减的规则"。

## R2 · `enable-chunked-prefill` 与 `enable-prefix-caching` 不能同时为 True

| 版本 | 证据 | 结论 |
|---|---|---|
| v0.4.2 | **运行期守卫**：`vllm/worker/model_runner.py:254–258` —— `and self.scheduler_config.chunked_prefill_enabled` → `"chunked prefill cannot be used with prefix caching "` | ✅ **运行期强制** |
| v0.5.5 | **运行期守卫**：`vllm/worker/model_runner.py:502–504` —— `if self.chunked_prefill_enabled and prefix_cache_hit: raise RuntimeError("chunked prefill cannot be used with prefix caching now.")` | ✅ **运行期强制** |
| v0.6.6 / v0.8.0 | 主 `model_runner.py` 中守卫**已移除**（仅 hpu/openvino runner 保留）；上游 PR #7753 加入对该组合的支持 | ❌ **已随支持移除** |
| v0.5.5 / v0.10.0 / v0.30.0 执行级 | **构造期**（`SchedulerConfig`/`CacheConfig`/`EngineArgs`）均**不报错** | ⚠️ 构造路径不可见（运行期守卫） |

> ⚠️ **2026-09-28 重大更正（经模拟审稿人 1 指出并本地复核确认）**：
> 本文早前版本据"配置参数名同现"启发式（`enable_chunked_prefill`+`enable_prefix_caching`）判定 R2"从未是代码约束/过度断言"——**该判定错误**。R2 在锚点版本（0.4.2/0.5.5）是**运行期强制**的真实约束（守卫用运行期变量 `prefix_cache_hit`，报错消息写 "prefix caching" 带空格，故词表启发式假阴性）；上游支持该组合后于 v0.6.6+ 移除。
> **修正后的判定：R2 = 真实约束 → 随上游支持而衰减（移除）**。这也暴露了**构造期证伪的边界**：运行期守卫必须运行期测试（对应论文的 `not-tested` 类别）。

**判定：R2 很可能从来就不是"代码约束"**——在 SCOOT 的两个原始锚点版本里，引擎源码都没有禁止两者同时开启；v0.5.5 的唯一交互是"未开 prefix caching 时自动开 chunked prefill"。
**谨慎声明**：不排除运行期存在性能层面的相互干扰（SCOOT 可能来自运维观察/文档），但**配置校验路径从未禁止该组合**；SCOOT 把它列为 "known constraint" 属于**人工知识的过度断言**。

> **论文含义（比"衰减"更强）**：人工约束不仅会**过期**，还可能**从一开始就与源码不符**。这直接支持"约束必须来自源码 + 必须执行证伪"的核心论点。

## R3 · 未开 chunked-prefill 时 `mtib >= max_model_len`

| 版本 | 源码证据 | 结论 |
|---|---|---|
| v0.5.5 | `vllm/config.py:927-936`：`if (self.max_num_batched_tokens < self.max_model_len and not self.chunked_prefill_enabled): raise ...` | ✅ 存在，**当时就是条件式** |
| **v0.5.5 执行级** | `chunked=False` 且 `mtib(2048) < max_model_len(4096)` → **ValueError（同构消息）**；对照（mtib 4096 ≥ max_model_len 4096）构造成功（`v0.5.5-exec.json`） | ✅ **执行级确认** |
| **v0.10.0 执行级** | 同构用例 → **ValidationError（同构消息）**；对照通过（`v0.10.0-exec.json`） | ✅ **执行级确认** |
| v0.30.0 | `vllm/config/scheduler.py:296-303`（同构条件）；执行证伪通过 | ✅ 存在，语义一致 |

**判定：R3 语义跨版本一致（我们此前"语义已变"的说法需要修正为"默认条件变了"）**：
- 规则本身（未开 chunked prefill ⇒ mtib ≥ max_model_len）在 0.5.5 就是条件式的；
- **实际约束力的变化来自默认值**：V1 默认开启 chunked prefill（v0.30.0 启动日志：`Chunked prefill is enabled with max_num_batched_tokens=...`），使该规则在默认配置下**几乎不触发**；
- 即：**规则没变，环境变了**——这也是"人工约束需要随版本重新评估适用性"的另一种形态。

---

## 汇总（对论文的口径修正）

| 规则 | 旧口径（v1 报告） | **修正后口径（本深查）** |
|---|---|---|
| R1 | 仍成立 | ✅ **跨 5 版本稳定存在**（v0.5.5 / v0.10.0 / v0.30.0 三版本执行级均强制） |
| R2 | 已失效（refuted） | 🔁 **2026-09-28 更正**：锚点版本（0.4.2/0.5.5）**运行期强制**（`worker/model_runner.py` 守卫），上游支持该组合后 **v0.6.6+ 移除** → **衰减（移除型）**；构造期检查不可见（暴露构造期证伪边界） |
| R3 | 仍成立但语义条件化 | ✅ **语义一致（0.5.5 即条件式；三版本执行级均强制）**；变化在默认值（V1 默认开 chunked prefill），**实际约束力显著下降** |

**一句话**：SCOOT 的 3 条人工约束中，**1 条从未在源码中成立、1 条因默认值变化而失去约束力、仅 1 条跨 5 版本稳定**——"人工约束不可靠"的证据比"衰减"更强。

---

*完成：2026-09-27 ｜ 证据：`vllm-versions/v0.4.2`、`v0.5.5` 源码 + `scoot-drift.json`（v0.30.0 执行）*
*⚠️ 待同步：S4 报告 §三、`scoot-drift.json` note、论文 §2.4/§4.3 口径*