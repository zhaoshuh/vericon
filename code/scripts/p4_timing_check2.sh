#!/usr/bin/env bash
CSV='/mnt/f/文献/AgentOps/实验记录/P4-并行-records-q8/optuna/p4-5d-q8-N-s1/trials.csv'
echo "== N s1 行数 =="; echo $(($(wc -l < "$CSV") - 1))
echo "== 前 2 / 后 2 行（number, start, complete, duration）=="
cut -d, -f1,3,4,5 "$CSV" | head -3
cut -d, -f1,3,4,5 "$CSV" | tail -2
echo ""
echo "== 目录 mtime =="
date -r '/mnt/f/文献/AgentOps/实验记录/P4-并行-records-q8/optuna/p4-5d-q8-N-s1' '+%H:%M:%S'
date -r '/mnt/f/文献/AgentOps/实验记录/optuna/p4-5d-q8-N-s1' '+%H:%M:%S' 2>/dev/null || echo "主目录无此 study"
