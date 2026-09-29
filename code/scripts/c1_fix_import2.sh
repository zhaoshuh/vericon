#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
p = "/mnt/f/文献/AgentOps/代码/scripts/c1_import_results.py"
t = open(p, encoding="utf-8").read()
t = t.replace("'human'", "'pass'").replace('"human"', '"pass"')
open(p, "w", encoding="utf-8", newline="").write(t)
print("剩余 'human' 次数:", t.count("human"))
PYEOF
~/.venvs/agentops-py311/bin/python /mnt/f/文献/AgentOps/代码/scripts/c1_import_results.py 2>&1 | tail -22
