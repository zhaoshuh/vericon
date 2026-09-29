"""AgentOps 实验代码包（S2 起）。

模块：
- record          统一实验记录格式（配置 → 指标 → 成本）
- backends.vidur  Vidur 仿真后端（本机默认；CPU 可跑）
- backends.vllm   真实 vLLM 后端（需 Linux + CC>=7.5 的 GPU；本机不可用）
- run_one         跑通"一条配置"的最小闭环
- tune            Optuna 调优（max_num_seqs / max_num_batched_tokens）
"""

__version__ = "0.2.0-s2"
