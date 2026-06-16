#!/bin/bash
# Docker 方式启动 Agent Tools Kit
# 需要先安装 Docker 和 docker-compose

set -e

echo "=== Agent Tools Kit (Docker) ==="

if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未安装 Docker"
    echo "请访问 https://docs.docker.com/get-docker/ 安装"
    echo ""
    echo "💡 你也可以用本地 Python 方式启动："
    echo "   ./run.sh"
    exit 1
fi

# 创建数据目录
mkdir -p data

# 构建并启动
echo "🚀 正在构建并启动服务..."
docker compose up -d --build

echo ""
echo "✅ 服务已启动！"
echo "  REST API:  http://localhost:8000/api"
echo "  健康检查:  http://localhost:8000/api/health"
echo "  MCP 端点:  http://localhost:8000/mcp  (SSE 协议)"
echo ""
echo "📦 数据目录: ./data/"
echo "📋 查看日志: docker compose logs -f"
echo "⏹  停止服务: docker compose down"
