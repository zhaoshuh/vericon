# Data dictionary

All records were produced by the scripts in `code/scripts/` (see `README.md`). Paths below are relative to the repository root.

## `graph/` — constraint graphs (JSON)

| File | Contents |
|---|---|
| `约束图-v1-ext.json` | **Main artifact**: 716 constraint nodes for vLLM v0.30.0. Each node carries `type` (implication / range / enum / arithmetic / inequality / mutual_exclusion / type), `expr`, `params`, `scope`, `severity`, `mechanism`, **`evidence[]` = one or more `{file, line, snippet}` entries**, and `validation` (status + how it was tested). Also includes `stats` (totals, by-type, by-scope, tiers 282+434) and `rejected` / `dropped_by_agent` lists. |
| `约束图-v1.json` | The 282-constraint core-tier graph (configuration/engine tiers) — frozen snapshot used by the gold-standard audits. |
| `约束图-sglang.json` | **420** constraint nodes for SGLang v0.5.20, same schema (`meta.commit` = v0.5.20 commit). |
| `约束图-model2.json` | Independent second-extractor graph (different LLM, same schema) used for the cross-model re-discovery check (97.2%). |
| `已验证约束.json` | vLLM v0.30.0 constraints confirmed by executing the real validation path (construction path; primary batch). |
| `已验证约束-跨引擎.json` | Cross-engine confirmation set: vLLM 113 (111 primary + 2 cross-model) and llama.cpp (2 confirmed / 6 refuted). |
| `参数清单.json` | Static parameter inventory for vLLM v0.30.0: 9,670 annotated fields (2,258 classes), 585 in `vllm/config/`, 242 in `EngineArgs`, 262 CLI-flag registrations (259 distinct names). |
| `P5-附加约束.json` | Two auxiliary rules used by the formalization/sampler demonstration (one execution-discovered load bound, one simulator-derived KV-capacity rule). |
| `llamacpp_constraints.json` | llama.cpp v0.5.0 execution tests: 17 cases covering 7 candidate rules (2 confirmed, 6 refuted). |
| `llamacpp_anchor.csv`, `llamacpp_anchor_5rep.csv` | Real throughput anchor grid (24 configurations; 2-repeat and 5-repeat runs; pp512/tg64 in tok/s). |
| `llamacpp_hello.json` | Sanity run for the llama.cpp binary (version/build/commit evidence). |

## `records/` — result files

| File / directory | Contents |
|---|---|
| `P1b-金标准样本*.json`, `P1b-标注结果*.json`, `P1b-300汇总.json`, `P1b-金标准-结果-300.md` | Gold-standard recall audit: 300 stratified sites (50 per tier per sample, fixed seeds), per-site labels (203 true constraints / 97 non-constraints), capture flags (exact / ±1 line), tier-wise and combined estimates (71.9% / 87.2%). |
| `P1b-标注一致性*.json` | Second independent labeling pass (120 sites) — raw agreement and Cohen's κ. |
| `P3-sglang抽检-独立审核.json` | SGLang quality audit: 40 type-stratified constraints re-checked + 20 blind re-audits (0 incorrect). |
| `P2-版本研究/` | Version-drift study: `v{0.4.2,0.5.5,0.6.6,0.8.0,0.10.0,0.30.0}-params.json` (static inventory per release, with commit) and `v{0.5.5,0.10.0}-exec.json` (execution re-checks), plus `SCOOT规则深查.md` (rule-level re-verification: runtime guard present in v0.4.2/v0.5.5, removed in v0.6.6+). |
| `S4验证/` | Falsification harness results for vLLM v0.30.0: per-case records (155 constructible cases), captured engine error text and exit codes. |
| `S5-报告.md`, `S5-汇总.md` | Three-arm tuning study (N/M/A, 20 seeds × 30 trials): per-seed costs, trials-to-target, charged invalid rates. |
| `S7-报告.md`, `S7-结果.csv` | Multi-workload transfer (3 traces) and the trace-independent threshold finding (`mtib ≤ 1008` fail / `≥ 1025` succeed on all traces). |
| `S8-llamaCpp调优/` | **Real-engine A≠M micro-study** (llama.cpp v0.5.0, Qwen2.5-1.5B, 216-combination space, 4 arms × 5 seeds × 20 trials = 400 real inference runs, trial-level interleaving + calibration): `trials-ext.csv`, `calibration-ext.csv`, `verification-ext*.csv`, `S8-ext-汇总.json`, `S8-ext-报告.md`. |
| `P4-报告.md`, `P4-结果.csv` | Dimension-scaling (2-D–6-D) summary used in the manuscript. |
| `S3-抽取报告.md`, `S3-约束抽取方法.md`, `S3-跨模型对比.json` | Extraction protocol description and cross-model re-discovery statistics (97.2% evidence-anchored re-discovery). |

## `code/`

* `code/agentops/` — the tuner package: `tune.py` (Optuna loop with arm presets), `constraint_sampler.py` (graph-driven sampler: parses constraint nodes, computes per-parameter feasible bounds from evaluable constraints, never emits violating assignments), `record.py` (append-only records with cross-process file locking), `paths.py`, `backends/` (Vidur simulator backend).
* `code/scripts/` — every script used in the study: static enumeration (`extract_params.py`, `scan_constraint_candidates.py`), version scanning (`analyze_versions.py`, `analyze_versions.py`), agent-extraction helpers, falsification harnesses (`run_s4_verify.sh`, `s4_verify_vllm.py`, `verify_r2_claim.sh`, `llamacpp_*`), tuning/analysis (`s5_*`, `analyze_s7.py`, `s8*`, `make_paper_figs.py`, `regen_*`), and the gold-standard audit tooling (`c1_*`).

## Notes on scope

* Vidur's per-study simulation outputs (plot dumps, per-request time series; >300 MB) are **not redistributed** — they are regenerated by re-running the tuning scripts with the bundled Optuna/analysis code and the Vidur package.
* Internal project-management files (progress notes, simulated reviews, labeling UI) are out of scope for this artifact.
