# 生产环境 Docker 启动脚本（Windows PowerShell）
Set-Location $PSScriptRoot
docker compose pull
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker compose up -d
