#!/usr/bin/env bash
set -euo pipefail
export LD_LIBRARY_PATH="$HOME/.venvs/agentops-py311/lib:${LD_LIBRARY_PATH:-}"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
exec python "/mnt/f/文献/AgentOps/代码/scripts/s6_llamacpp_probe.py"
