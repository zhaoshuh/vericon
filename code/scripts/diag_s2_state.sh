#!/usr/bin/env bash
# S2 状态诊断：conda/venv 依赖 / 上次记录副本 / 产物目录 / 脚本换行符 / Vidur 仓库
set -u
ROOT="/mnt/f/文献/AgentOps"

echo "==[1] conda 与 venv =="
ls -l "$HOME/miniconda3/etc/profile.d/conda.sh" 2>&1 | head -2
ls -d "$HOME/.venvs/agentops-py311" 2>&1
"$HOME/.venvs/agentops-py311/bin/python" - <<'PY'
import sys
print("python:", sys.version.split()[0])
for m in ("numpy", "pandas", "sklearn", "optuna"):
    try:
        mod = __import__(m)
        print(f"{m}: {getattr(mod, '__version__', '?')}")
    except Exception as e:
        print(f"{m}: MISSING ({e})")
PY

echo ""
echo "==[2] 上次记录的副本（third_party/vidur/agentops_record.json，前 500 字节）=="
head -c 500 "$ROOT/代码/third_party/vidur/agentops_record.json" 2>&1
echo ""

echo ""
echo "==[3] 仿真输出与 optuna 目录 =="
ls -la "$ROOT/实验记录/仿真输出/" 2>&1 | head -10
ls -la "$ROOT/实验记录/optuna/" 2>&1 | head -10

echo ""
echo "==[4] 包装脚本换行符（应为 ASCII text，不含 CRLF）=="
file "$ROOT/代码/scripts/run_one.sh" "$ROOT/代码/scripts/run_tune.sh" 2>&1

echo ""
echo "==[5] Vidur 仓库状态 =="
git -C "$ROOT/代码/third_party/vidur" log -1 --format="%h %cd %s" 2>&1
echo "-- processed_traces --"
ls "$ROOT/代码/third_party/vidur/data/processed_traces/" 2>&1 | head -20
echo "-- profiling 计算数据 --"
ls "$ROOT/代码/third_party/vidur/data/profiling/compute/" 2>&1 | head -10
echo "-- 预测器磁盘缓存 --"
ls -la "$ROOT/代码/third_party/vidur/cache/" 2>&1 | head -10

echo ""
echo "==[6] CPU / 内存 =="
nproc 2>&1
free -h 2>&1 | head -2

echo ""
echo "DIAG_DONE"
