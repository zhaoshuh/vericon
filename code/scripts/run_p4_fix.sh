#!/usr/bin/env bash
# P4 修复扫描：重跑因 sqlite 瞬时锁 / runs.csv 损坏而失败的 2d-N 臂 studies
# 前置：主扫描必须已结束（避免并发写）；本脚本会先删除主 DB 中的残留 study 再重跑。
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled

# 0) 安全检查：主扫描是否仍在运行
if pgrep -f "agentops.tune" > /dev/null; then
  echo "!! 检测到仍在运行的 agentops.tune，终止修复扫描（请等主扫描结束后再跑）"
  exit 1
fi

# 1) 清理主 DB 中的残留 study
python - <<'PY'
import optuna
storage = "sqlite:////mnt/f/文献/AgentOps/实验记录/optuna/studies.db"
for s in (3, 5, 6, 7, 8, 9, 10):
    name = f"p4-2d-q12-N-s{s}"
    try:
        optuna.delete_study(study_name=name, storage=storage)
        print("deleted", name)
    except Exception as e:
        print("skip", name, type(e).__name__)
PY

# 2) 重跑（新 record.py：文件锁 + 原子替换）
for s in 3 5 6 7 8 9 10; do
  echo "=== p4-fix 2d arm=N seed=$s [$(date +%H:%M:%S)] ==="
  python -m agentops.tune --arm N --seed "$s" --n-trials 30 --space-mode 2d \
    --qps 12.0 --num-requests 384 --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
    --study-name "p4-2d-q12-N-s$s" || echo "!! fail s$s"
done
echo "P4 FIX SWEEP DONE"
