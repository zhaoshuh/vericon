#!/usr/bin/env bash
# 诊断 Vidur editable 安装为何 import 失败
source "$HOME/.venvs/agentops/bin/activate"
SP="$HOME/.venvs/agentops/lib/python3.14/site-packages"

echo "--- pth 内容 ---"
cat "$SP/__editable__.vidur-0.0.1.pth"
echo
echo "--- finder 前 30 行 ---"
head -30 "$SP/__editable___vidur_0_0_1_finder.py"
echo
echo "--- 直接 import finder ---"
python - <<'PY'
import importlib, traceback
try:
    m = importlib.import_module("__editable___vidur_0_0_1_finder")
    print("finder OK; MAPPING 前 3 项:")
    for k, v in list(m.MAPPING.items())[:3]:
        print(" ", k, "->", v)
except Exception:
    traceback.print_exc()
PY
echo
echo "--- import vidur 的真实报错 ---"
python - <<'PY'
import traceback
try:
    import vidur
    print("vidur OK:", vidur.__file__)
except Exception:
    traceback.print_exc()
PY
