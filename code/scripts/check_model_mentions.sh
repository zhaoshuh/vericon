#!/usr/bin/env bash
T=/mnt/f/文献/AgentOps/论文/latex/main.tex
echo "=== 论文中出现的模型/厂商名 ==="
grep -n -i 'openai\|gpt\|claude\|sonnet\|gemini\|glm\|qwen\|deepseek\|model instance\|different LLM\|sub-agent' "$T" | head -20
echo ""
echo "=== 封面信中的模型提及 ==="
grep -n -i 'openai\|gpt\|claude\|glm\|model' /mnt/f/文献/AgentOps/论文/latex/cover-letter.txt | head -10
echo ""
echo "=== S3 抽取报告里的 agent 模型 ==="
grep -n -i 'model\|模型\|claude\|gpt\|glm' /mnt/f/文献/AgentOps/实验记录/S3-抽取报告.md | head -12
