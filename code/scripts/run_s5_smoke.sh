#!/usr/bin/env bash
# S5 冒烟：dry-run + 三臂各 3 trials
set -euo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd "/mnt/f/文献/AgentOps/代码"
export WANDB_MODE=disabled

echo "===== dry-run 5d (arm N) ====="
python -m agentops.tune --space-mode 5d --arm N --dry-run --n-trials 5 --seed 999

for arm in N M A; do
  echo ""
  echo "===== smoke arm $arm (3 trials) ====="
  python -m agentops.tune --space-mode 5d --arm "$arm" --seed 999 --n-trials 3 \
      --study-name "s5-smoke2-$arm"
done
echo ""
echo "SMOKE DONE"
