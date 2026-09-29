#!/usr/bin/env bash
# 调试：为什么 itl 提取为 None
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
export WANDB_MODE=disabled
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd "/mnt/f/文献/AgentOps/代码"
python - <<'PY'
import sys
sys.path.insert(0, "/mnt/f/文献/AgentOps/代码")

from agentops.backends.vidur_backend import VidurRunSpec, _install_predictor_cache, _ensure_vidur_on_path

_install_predictor_cache()

from vidur.config import SimulationConfig
from vidur.simulator import Simulator
from vidur.utils.random import set_seeds

spec = VidurRunSpec(max_num_seqs=64, max_num_batched_tokens=2048, num_requests=16, qps=8)

# 直接构造配置（复用 backend 的 CLI 组装）
import os, tempfile, time
from pathlib import Path
from agentops.backends.vidur_backend import _build_cli_args
from agentops.paths import vidur_dir
from contextlib import contextmanager

@contextmanager
def chdir(p):
    old = os.getcwd(); os.chdir(p)
    try: yield
    finally: os.chdir(old)

out_base = Path(tempfile.mkdtemp(prefix="agentops_dbg_"))
with chdir(vidur_dir()):
    old_argv = sys.argv
    sys.argv = ["dbg"] + _build_cli_args(spec, out_base)
    try:
        cfg = SimulationConfig.create_from_cli_args()
    finally:
        sys.argv = old_argv
    set_seeds(cfg.seed)
    from agentops.backends.vidur_backend import _reset_vidur_entity_counters
    _reset_vidur_entity_counters()
    sim = Simulator(cfg)
    sim.run()

store = sim._metric_store
from vidur.metrics.constants import TokenMetricsTimeDistribution as T
d = store._token_metrics_time_distribution
print("dict keys:", [k.name for k in d.keys()])
obj = d[T.DECODE_TOKEN_EXECUTION_PLUS_PREMPTION_TIME]
print("type:", type(obj))
sk = obj._sketch
print("sketch:", type(sk))
print("has count attr:", hasattr(sk, "count"), "| _count:", getattr(sk, "_count", None))
try:
    print("quantile 0.9:", sk.get_quantile_value(0.9))
except Exception as e:
    import traceback; traceback.print_exc()

# 直接测 _extract_metrics（复现 run() 里的调用路径）
from agentops.backends.vidur_backend import _extract_metrics
m = _extract_metrics(sim, spec)
print("itl_p50_s =", m["itl_p50_s"], "| itl_p90_s =", m["itl_p90_s"], "| itl_p99_s =", m["itl_p99_s"])
print("itl_error =", m.get("itl_error"))
PY
