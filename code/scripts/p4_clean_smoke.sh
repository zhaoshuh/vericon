#!/usr/bin/env bash
# 删除 6d 冒烟产生的两个 study（避免全量运行后 trial 数不一致）
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
python - <<'PY'
import optuna
storage = "sqlite:////mnt/f/文献/AgentOps/实验记录/optuna/studies.db"
for name in ("p4-6d-q12-N-s1", "p4-6d-q12-A-s1"):
    try:
        optuna.delete_study(study_name=name, storage=storage)
        print("deleted", name)
    except Exception as e:
        print("skip", name, type(e).__name__)
PY
