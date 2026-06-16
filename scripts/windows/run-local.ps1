# 本地 Python 方式启动 Agent Tools Kit（Windows PowerShell）
# 前置条件：Python 3.10+
# 注意：Windows 上必须用 python -m uvicorn（裸 uvicorn 可能找不到命令）

param(
    [switch]$NoReload
)

$ProjectDir = Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent
Set-Location $ProjectDir

Write-Host "=== Agent Tools Kit (Local Python) ===" -ForegroundColor Cyan

# 检查 Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "错误: 未安装 Python" -ForegroundColor Red
    Write-Host "请访问 https://www.python.org/downloads/ 安装 Python 3.10 或更高版本"
    exit 1
}

# 检查依赖
python -c "import uvicorn" 2>$null
if (-not $?) {
    Write-Host "正在安装依赖..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if (-not $?) { exit 1 }
}

# 创建数据目录
if (-not (Test-Path data)) { New-Item -ItemType Directory -Path data -Force | Out-Null }

Write-Host "正在启动服务..." -ForegroundColor Green
Write-Host ""

$reloadArg = "--reload"
if ($NoReload) { $reloadArg = "" }

python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 $reloadArg