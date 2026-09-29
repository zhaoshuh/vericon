#!/usr/bin/env bash
echo "== miniconda libgomp =="
find "$HOME/miniconda3" -name "libgomp.so*" 2>/dev/null | head -5
echo "== agentops env libgomp =="
find "$HOME/.venvs/agentops-py311" -name "libgomp.so*" 2>/dev/null | head -5
echo "== system libgomp =="
find /usr -name "libgomp.so*" 2>/dev/null | head -5
echo "== ldconfig =="
ldconfig -p 2>/dev/null | grep -i gomp | head -5 || echo "none in ldconfig"
