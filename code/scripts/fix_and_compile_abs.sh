#!/usr/bin/env bash
# 修正 a_batch_compile.sh 里的摘要计数口径（保留命令参数内容）
~/.venvs/agentops-py311/bin/python - <<'PYEOF'
p = "/mnt/f/文献/AgentOps/代码/scripts/a_batch_compile.sh"
t = open(p, encoding="utf-8").read()
old = """import re
lines = open('/mnt/f/文献/AgentOps/论文/latex/main.tex', encoding='utf-8').read().splitlines()
for i, l in enumerate(lines):
    if l.strip() == r'\\begin{abstract}':
        body = lines[i+1]
        body = re.sub(r'\\\\[a-zA-Z]+\\*?(\\[[^\\]]*\\])?(\\{[^{}]*\\})?', ' ', body)
        body = re.sub(r'[{}\\\\~$]', ' ', body)
        print('abstract words:', len([w for w in body.split() if any(c.isalnum() for c in w)]), '(<=250)')
        break"""
new = """import re
lines = open('/mnt/f/文献/AgentOps/论文/latex/main.tex', encoding='utf-8').read().splitlines()
def _cnt(latex):
    s = latex
    s = re.sub(r'\\\\textbf\\{([^{}]*)\\}', r'\\1', s)
    s = re.sub(r'\\\\emph\\{([^{}]*)\\}', r'\\1', s)
    s = re.sub(r'\\\\code\\{([^{}]*)\\}', r'\\1', s)
    s = re.sub(r'\\\\%', '%', s)
    s = re.sub(r'\\\\[a-zA-Z]+(\\[[^\\]]*\\])?(\\{[^{}]*\\})?', ' ', s)
    s = re.sub(r'[{}$\\\\]', ' ', s)
    return len([w for w in s.split() if any(c.isalnum() for c in w)])
for i, l in enumerate(lines):
    if l.strip() == r'\\begin{abstract}':
        print('abstract words (correct):', _cnt(lines[i+1]), '(<=250)')
        break"""
if old in t:
    t = t.replace(old, new)
    open(p, "w", encoding="utf-8", newline="").write(t)
    print("checker 已修正")
else:
    print("（未匹配，跳过修正）")
PYEOF
echo ""
echo "=== 重编译 + 检查 ==="
bash /mnt/f/文献/AgentOps/代码/scripts/a_batch_compile.sh 2>&1 | head -12
