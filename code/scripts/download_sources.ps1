# 下载 P2/P3 所需源码：SGLang v0.5.20 + vLLM 历史版本（0.4.2 / 0.5.5 / 0.6.6 / 0.8.0 / 0.10.0）
$base = "F:\文献\AgentOps\代码\third_party"
$jobs = @(
  @{url="https://codeload.github.com/sgl-project/sglang/tar.gz/refs/tags/v0.5.20"; dir="$base\sglang-v0.5.20"; name="sglang-v0.5.20"},
  @{url="https://codeload.github.com/vllm-project/vllm/tar.gz/refs/tags/v0.4.2";  dir="$base\vllm-versions\v0.4.2";  name="vllm-v0.4.2"},
  @{url="https://codeload.github.com/vllm-project/vllm/tar.gz/refs/tags/v0.5.5";  dir="$base\vllm-versions\v0.5.5";  name="vllm-v0.5.5"},
  @{url="https://codeload.github.com/vllm-project/vllm/tar.gz/refs/tags/v0.6.6";  dir="$base\vllm-versions\v0.6.6";  name="vllm-v0.6.6"},
  @{url="https://codeload.github.com/vllm-project/vllm/tar.gz/refs/tags/v0.8.0";  dir="$base\vllm-versions\v0.8.0";  name="vllm-v0.8.0"},
  @{url="https://codeload.github.com/vllm-project/vllm/tar.gz/refs/tags/v0.10.0"; dir="$base\vllm-versions\v0.10.0"; name="vllm-v0.10.0"}
)
foreach ($j in $jobs) {
  $tmp = "$env:TEMP\$($j.name).tar.gz"
  try {
    Invoke-WebRequest -Uri $j.url -OutFile $tmp -UseBasicParsing -TimeoutSec 900 -ErrorAction Stop
    "downloaded(direct): $($j.name)"
  } catch {
    try {
      Invoke-WebRequest -Uri $j.url -OutFile $tmp -Proxy "http://127.0.0.1:7877" -UseBasicParsing -TimeoutSec 900 -ErrorAction Stop
      "downloaded(proxy): $($j.name)"
    } catch {
      "FAILED download: $($j.name)  $($_.Exception.Message)"
      continue
    }
  }
  New-Item -ItemType Directory -Force -Path $j.dir | Out-Null
  tar -xzf $tmp -C $j.dir --strip-components=1
  $n = (Get-ChildItem $j.dir -ErrorAction SilentlyContinue | Measure-Object).Count
  "extracted: $($j.name)  entries=$n"
}
"ALL DOWNLOADS DONE"
