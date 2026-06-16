# Docker 方式启动 Agent Tools Kit（Windows PowerShell）
# 前置条件：Docker Desktop

$ProjectDir = Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent
Set-Location $ProjectDir

Write-Host "=== Agent Tools Kit (Docker) ===" -ForegroundColor Cyan

# 检查 Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未安装 Docker" -ForegroundColor Red
    Write-Host "请访问 https://docs.docker.com/get-docker/ 安装 Docker Desktop"
    Write-Host ""
    Write-Host "提示: 你也可以用本地 Python 方式启动："
    Write-Host "   .\scripts\windows\run-local.ps1"
    exit 1
}

# 创建数据目录
if (-not (Test-Path data)) { New-Item -ItemType Directory -Path data -Force | Out-Null }

Write-Host "正在构建并启动服务..." -ForegroundColor Green
docker compose up -d --build

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "服务已启动！" -ForegroundColor Green
Write-Host "  REST API:  http://localhost:8000/api"
Write-Host "  健康检查:  http://localhost:8000/api/health"
Write-Host "  MCP 端点:  http://localhost:8000/mcp  (SSE 协议)"
Write-Host ""
Write-Host "数据目录: .\data\"
Write-Host "查看日志: docker compose logs -f"
Write-Host "停止服务: docker compose down"