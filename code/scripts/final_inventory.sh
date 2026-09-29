#!/usr/bin/env bash
echo "== 后台进程（应为 0） =="
pgrep -f "agentops.tune" | wc -l
echo ""
echo "== 全部 study 规模统计 =="
for p in s5 s6 s7 p4 p5; do
  n=$(ls -d /mnt/f/文献/AgentOps/实验记录/optuna/${p}*/ 2>/dev/null | wc -l)
  echo "  ${p}*: $n studies"
done
echo "  合计: $(ls -d /mnt/f/文献/AgentOps/实验记录/optuna/*/ 2>/dev/null | wc -l) studies"
echo ""
echo "== 最终日志标记 =="
grep -l "DONE" /mnt/f/文献/AgentOps/实验记录/*.log 2>/dev/null | head -6
grep -h "DONE" /mnt/f/文献/AgentOps/实验记录/*.log 2>/dev/null | tail -6
echo ""
echo "== runs.jsonl 行数 =="
wc -l < /mnt/f/文献/AgentOps/实验记录/runs.jsonl
