$repo = "F:\文献\AgentOps\论文Q4\复现包\llm-serving-config-constraints"
Write-Output "== remote =="
git -C $repo remote -v
Write-Output "== 本地作者配置 =="
git -C $repo config user.name
git -C $repo config user.email
Write-Output "== 最近提交 =="
git -C $repo log --oneline -5
Write-Output "== README 头部 =="
if (Test-Path "$repo\README.md") { Get-Content "$repo\README.md" -TotalCount 10 }
Write-Output "== 分支 =="
git -C $repo branch -a
Write-Output "== 凭据测试（ls-remote；不应提示输入密码）=="
$env:GIT_TERMINAL_PROMPT = "0"
git -C $repo ls-remote --heads origin 2>&1 | Select-Object -First 5
