#!/bin/bash
# 本地 Python 方式启动 Agent Tools Kit
# 需要先安装 Python 3.10+

set -e

echo "=== Agent Tools Kit (Local Python) ==="

# 检查 Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ 错误: 未安装 Python"
    echo "请访问 https://www.python.org/downloads/ 安装 Python 3.10 或更高版本"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)

# 检查 uvicorn
if ! $PYTHON -c "import uvicorn" 2>/dev/null; then
    echo "📦 正在安装依赖..."
    $PYTHON -m pip install -r requirements.txt
fi

# 创建数据目录
mkdir -p data

echo "🚀 正在启动服务..."
echo ""
$PYTHON -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
