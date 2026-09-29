#!/usr/bin/env bash
echo "== tune 进程及其 study =="
for p in $(pgrep -f "agentops.tune"); do
  tr '\0' ' ' < "/proc/$p/cmdline" | grep -o -- "--study-name [^ ]*" || echo "  (no study-name)"
done
