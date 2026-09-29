#!/usr/bin/env bash
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
python /mnt/f/文献/AgentOps/代码/scripts/make_p4_figs.py
