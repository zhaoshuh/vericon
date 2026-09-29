#!/usr/bin/env bash
echo "== 直测 TUNA CTAN 下载速度（15 秒窗口） =="
curl -o /dev/null --max-time 15 -w "speed: %{speed_download} B/s, size: %{size_download} bytes, code: %{http_code}\n" \
  "https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/tlnet/archive/amsfonts.tar.xz" 2>&1 || echo "curl 失败/超时"
echo ""
echo "== 对比：TUNA PyPI（此前很快） =="
curl -o /dev/null --max-time 10 -w "speed: %{speed_download} B/s, code: %{http_code}\n" \
  "https://pypi.tuna.tsinghua.edu.cn/simple/pip/" 2>&1 || echo "curl 失败/超时"
echo ""
echo "== 对比：GitHub codeload（此前很快） =="
curl -o /dev/null --max-time 10 -w "speed: %{speed_download} B/s, code: %{http_code}\n" \
  -r 0-500000 "https://codeload.github.com/vllm-project/vllm/tar.gz/refs/tags/v0.1.0" 2>&1 || echo "curl 失败/超时"
