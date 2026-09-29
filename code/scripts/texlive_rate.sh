#!/usr/bin/env bash
D=$(ls -d /tmp/M2* | head -1)
A=$(du -sb "$D" | cut -f1)
S=$(find "$D" -type f | wc -l)
sleep 60
B=$(du -sb "$D" | cut -f1)
S2=$(find "$D" -type f | wc -l)
echo "60 秒增量: $(( (B - A) / 1024 )) KB（文件数 $S -> $S2）"
echo "总下载: $(( B / 1048576 )) MB"
echo "按此速率估算剩余（假设需 400MB）: $(( (400*1048576 - B) / ( (B - A) / 60 + 1) / 60 )) 分钟"
