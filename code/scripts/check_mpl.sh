#!/usr/bin/env bash
"$HOME/.venvs/agentops-py311/bin/python" - <<'PY'
import sys
try:
    import matplotlib
    print("matplotlib", matplotlib.__version__)
except Exception as e:
    print("NO matplotlib:", e)
try:
    import numpy, pandas
    print("numpy", numpy.__version__, "pandas", pandas.__version__)
except Exception as e:
    print("deps issue:", e)
PY
