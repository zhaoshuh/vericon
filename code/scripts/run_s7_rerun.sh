#!/usr/bin/env bash
# S7 重跑（修正协议：所有 trace 统一 tokens_min=1024——已由失败分布证实为真实阈值）
# 先杀掉旧轨（4096/7500 错误协议），清理其 study，再以 1024 重跑 4 臂 × 10 种子 × 2 trace
set -uo pipefail
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate "$HOME/.venvs/agentops-py311"
if [ -d "$HOME/vidur-fast/vidur" ]; then export AGENTOPS_VIDUR="$HOME/vidur-fast"; fi
cd /mnt/f/文献/AgentOps/代码
export WANDB_MODE=disabled

MAIN=/mnt/f/文献/AgentOps/实验记录

echo "== kill 旧 S7 轨 =="
pkill -f run_s7_transfer.sh 2>/dev/null || true
pkill -f "agentops.tune" 2>/dev/null || true
sleep 3

echo "== 清理错误协议 study（保留 A1024 对照） =="
python - <<'PY'
import optuna, shutil, os
storage = "sqlite:////mnt/f/文献/AgentOps/实验记录/optuna/studies.db"
for tag in ("arxiv", "code"):
    for arm in ("N", "S", "M", "A"):
        for s in range(1, 11):
            name = f"s7-{tag}-{arm}-seed{s}"
            try:
                optuna.delete_study(study_name=name, storage=storage)
            except Exception:
                pass
            d = f"/mnt/f/文献/AgentOps/实验记录/optuna/{name}"
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
print("cleanup done", flush=True)
PY

is_done() {
  local f="$MAIN/optuna/$1/trials.csv"
  if [ -f "$f" ]; then
    local n
    n=$(($(wc -l < "$f") - 1))
    [ "$n" -ge 30 ] && return 0
  fi
  return 1
}

run_trace() {  # tag trace
  local tag=$1 trace=$2
  local rec="/tmp/agentops-s7b-$tag"
  mkdir -p "$rec"
  for arm in N S M A; do
    for s in 1 2 3 4 5 6 7 8 9 10; do
      local name="s7-$tag-$arm-seed$s"
      if is_done "$name"; then echo "[$tag] skip $name"; continue; fi
      echo "[$tag] $arm s$s $(date +%H:%M:%S)"
      AGENTOPS_RECORDS="$rec" python -m agentops.tune --arm "$arm" --seed "$s" --n-trials 30 \
        --space-mode 5d --qps 12.0 --num-requests 384 \
        --slo-ttft-p90-s 1.0 --slo-tpot-p90-s 0.1 \
        --tokens-min 1024 --length-trace "$trace" \
        --study-name "$name" || echo "!! fail $name"
      if [ -d "$rec/optuna/$name" ]; then
        rm -rf "$MAIN/optuna/$name"
        cp -r "$rec/optuna/$name" "$MAIN/optuna/"
      fi
    done
  done
  echo "[$tag] done $(date +%H:%M:%S)"
}

run_trace arxiv arxiv_summarization_stats_llama2_tokenizer_filtered_v2.csv &
T1=$!
run_trace code splitwise_code.csv &
T2=$!
wait $T1
wait $T2
echo "S7 RERUN DONE [$(date +%H:%M:%S)]"
