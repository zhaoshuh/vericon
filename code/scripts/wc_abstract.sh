#!/usr/bin/env bash
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
import re
lines = open('/mnt/f/文献/AgentOps/论文/latex/main.tex', encoding='utf-8').read().splitlines()
body = lines[43]  # line 44 (0-based 43)
body = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?', ' ', body)
body = re.sub(r'[{}\\~$]', ' ', body)
words = [w for w in body.split() if any(c.isalnum() for c in w)]
print('abstract words:', len(words))
PYEOF
