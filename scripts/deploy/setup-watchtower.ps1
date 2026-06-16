# 飞牛NAS 一键配置 Watchtower 自动更新（Windows PowerShell 版）
# Watchtower 会自动检测 GHCR 上的新镜像并拉取重启
#
# 前置条件：
#   1. NAS 上已安装 Docker
#   2. 已登录 ghcr.io
#
# 注意：此脚本通过 SSH 在 NAS 上执行命令，或直接在 Windows Docker 环境运行

param(
    [string]$Image,
    [string]$ComposeDir = (Get-Location).Path
)

Write-Host "=== Agent Tools Kit — Watchtower 自动更新配置 ===" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未安装 Docker" -ForegroundColor Red
    exit 1
}

# 镜像名
if (-not $Image) {
    $Image = Read-Host "请输入 GitHub 镜像名（如 ghcr.io/你的用户名/agent-tools-kit）"
}
Write-Host "目标镜像: $Image" -ForegroundColor Yellow

# ghcr 登录检查
Write-Host "检查 ghcr.io 登录状态..." -ForegroundColor Yellow
$result = docker pull "${Image}:latest" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "需要先登录 ghcr.io" -ForegroundColor Yellow
    Write-Host "步骤:" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://github.com/settings/tokens" -ForegroundColor Yellow
    Write-Host "  2. 创建 Classic Token，权限勾选 read:packages" -ForegroundColor Yellow
    Write-Host "  3. 运行: echo '你的_TOKEN' | docker login ghcr.io -u 你的GitHub用户名 --password-stdin" -ForegroundColor Yellow
    Read-Host "登录完成后按 Enter 继续"
}

# Compose 目录
if (-not (Test-Path "$ComposeDir\docker-compose.yml")) {
    Write-Host "未找到 docker-compose.yml，将在 $ComposeDir 创建一份" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $ComposeDir -Force | Out-Null
    @"
services:
  toolkit:
    image: $Image
    container_name: agent_tools_kit
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - TOOLKIT_DB=/app/data/toolkit.db
    restart: unless-stopped
"@ | Set-Content "$ComposeDir\docker-compose.yml"
    Write-Host "docker-compose.yml 已创建" -ForegroundColor Green
}

# 首次启动
Write-Host "首次启动容器..." -ForegroundColor Green
Set-Location $ComposeDir
docker compose up -d

# 启动 Watchtower
Write-Host "启动 Watchtower 自动更新容器..." -ForegroundColor Green
Write-Host "   - 检测间隔: 300 秒（5 分钟）" -ForegroundColor Gray
Write-Host "   - 自动清理旧镜像" -ForegroundColor Gray

docker run -d `
    --name watchtower `
    --restart unless-stopped `
    -v /var/run/docker.sock:/var/run/docker.sock `
    ghcr.io/containrrr/watchtower:latest `
    --interval 300 `
    --cleanup `
    agent_tools_kit

Write-Host ""
Write-Host "Watchtower 已启动！" -ForegroundColor Green
Write-Host "查看日志: docker logs -f watchtower" -ForegroundColor Cyan
Write-Host "停止自动更新: docker stop watchtower; docker rm watchtower" -ForegroundColor Cyan