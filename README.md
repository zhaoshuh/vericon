# VeriCon — Artifact for "Mining, Falsifying, and Injecting Configuration Constraints for LLM Inference Engines"

Replication package for the manuscript submitted to **IEEE Transactions on Software Engineering** (single author: Shuheng Zhao, Independent Researcher, zshbdfdc@163.com).

**One-line summary.** Hand-written configuration knowledge for LLM inference engines *decays*; we mine constraints from engine **source** (with verbatim `file:line` evidence), **falsify** them by executing the engine's real validation path, and **inject** the verified set into a Bayesian tuner.

---

## Headline results (all reproducible on a 4-core CPU laptop, zero GPU, ¥0)

| Result | Value |
|---|---|
| vLLM v0.30.0 constraints extracted | **716** (282 core tiers + 434 full-coverage extension), 100% with `file:line` evidence |
| Confirmed by executing the real engine (construction path) | **113** (111 primary + 2 cross-model), from 155 executed cases |
| SGLang v0.5.20 constraints extracted | **420** |
| llama.cpp v0.5.0 execution tests | **2 constraints confirmed**, **6 folk rules refuted** |
| Recall (300-site gold standard) | **71.9%** exact / **87.2%** within ±1 line; design-weighted 50.8%/59.5% (site-level) and **53.0%/63.2%** (constraint-level) |
| Independent human labeler (150 sites) | κ = **0.53** vs evaluator, **0.68** vs third blind pass; ±1 capture **84.8%** (equal-weight) |
| Tuning cost reduction (8,000+ simulated trials) | **−48.6%** (CI [46.7, 50.0]); 43.5–50.9% across 2-D–6-D spaces |
| Real-engine micro-study (llama.cpp, 1.5B, 216-combination space, 4 arms × 400 runs) | invalid trials: **A 0%** / S 5% (online learning) / M 12% (folk rule) / N 17% (none); cost **A < S (−13.0%) < M (−26.5%) < N (−33.8%)** |
| Version drift | of SCOOT's three published rules: 1 stable, 1 runtime guard **removed upstream** (v0.6.6+), 1 dormant under changed defaults |

---

## Repository layout

```
graph/      Constraint graphs with per-node evidence & validation status (vLLM, SGLang, llama.cpp, cross-model)
records/    Result/analysis files: recall audits, version-drift study, falsification cases,
            tuning summaries (S5/S7), and the llama.cpp real-engine study (S8)
code/       The pipeline: agentops package (tuner + constraint sampler) and all scripts
paper/      LaTeX source, compiled PDF, and figures of the manuscript
```

See **`DATA-DICTIONARY.md`** for a file-by-file description.

---

## How to reproduce

**Hardware.** Everything runs on a 4-core x86 CPU laptop (Intel i5-7300HQ, 23.7 GB RAM) with **no GPU** and no paid services.

**Software.** Python 3.11 (`numpy`, `optuna`, `matplotlib`, `pymupdf`, `sympy`); a TeX Live installation for the paper; optionally `llama.cpp` (build 11194) for the real-engine study.

**Third-party sources used** (not redistributed here; fetch the exact versions):

| Component | Version | Identifier |
|---|---|---|
| vLLM | v0.30.0 | commit `ced6857afa0ea7b2e3f0846a62e1394e90f15607` |
| vLLM (historic, drift study) | v0.4.2 / v0.5.5 / v0.6.6 / v0.8.0 / v0.10.0 | see `records/P2-版本研究/*-params.json` |
| SGLang | v0.5.20 | tag v0.5.20 → commit `94602c9c2b7cbdb8efd5c52802dac6a1c180089e` |
| llama.cpp | 0.5.0-dev | build 11194, commit `9f70b2cec` |
| Vidur (simulator) | MLsys'24 | `third_party/vidur` upstream |
| Model (real-engine study) | Qwen2.5-1.5B-Instruct Q4_K_M (and 0.5B for the anchor grid) | GGUF from the Qwen release | 

**Typical commands** (scripts live in `code/scripts/`):

```bash
# static enumeration + candidate generation (vLLM v0.30.0)
python code/scripts/extract_params.py        # parameter inventory
python code/scripts/scan_constraint_candidates.py   # assert / if-raise candidates
python code/scripts/analyze_versions.py      # cross-version churn (drift study)

# falsification of constructible constraints (real engine validation path)
bash code/scripts/run_s4_verify.sh           # vLLM v0.30.0 construction path
python code/scripts/llama_bench_smoke.sh     # llama.cpp execution anchor

# tuning studies (simulator) and analyses
python code/scripts/tune.py --sampler-graph graph/约束图-v1-ext.json ...
python code/scripts/s5_analyze.py            # three-arm study
python code/scripts/analyze_s7.py            # multi-workload transfer

# real-engine A≠M micro-study (400 real inference runs)
python code/scripts/s8c_llamacpp_ext.py      # run
python code/scripts/s8d_analyze_ext.py       # analyze
```

Notes: scripts use absolute WSL paths from the authors' environment in a few places; adjust the `ROOT` constant to your checkout. The simulator data for Vidur lives alongside the upstream Vidur package and is not redistributed.

---

## Data & code availability

* Code: **MIT** (see `LICENSE`).
* Data, constraint graphs, and result records: **CC BY 4.0**.
* Issues and questions are welcome via the repository's issue tracker.

## Citation

If you use these artifacts, please cite the manuscript:

> Shuheng Zhao. *VeriCon: Mining, Falsifying, and Injecting Configuration Constraints for LLM Inference Engines.* Manuscript submitted to IEEE Transactions on Software Engineering, 2026.
