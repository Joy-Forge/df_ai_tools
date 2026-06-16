#!/bin/bash
# 飞牛NAS 一键配置 Watchtower 自动更新
# Watchtower 会自动检测 GHCR 上的新镜像并拉取重启
#
# 前置条件：
#   1. 已在 NAS 上安装 Docker
#   2. 已登录 ghcr.io（参见下方 ghcr-login 步骤）
#
# 使用方式：
#   chmod +x setup-watchtower.sh
#   ./setup-watchtower.sh

set -e

echo "=== Agent Tools Kit — Watchtower 自动更新配置 ==="
echo ""

# ---------- 检查 Docker ----------
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未安装 Docker"
    exit 1
fi

# ---------- 获取镜像名 ----------
REPO_URL=$(git config --get remote.origin.url 2>/dev/null || echo "")
if [[ "$REPO_URL" =~ github\.com[/:](.+)\.git$ ]]; then
    REPO="${BASH_REMATCH[1],,}"  # GitHub 要求镜像名全小写
    IMAGE="ghcr.io/${REPO}/agent-tools-kit"
else
    echo "⚠️  无法从 git remote 推断仓库名"
    read -rp "请输入 GitHub 镜像名（如 ghcr.io/你的用户名/agent-tools-kit）: " IMAGE
fi

echo "📦 目标镜像: $IMAGE"
echo ""

# ---------- ghcr.io 登录提示 ----------
echo "🔑 检查 ghcr.io 登录状态..."
if ! docker pull "$IMAGE:latest" --quiet 2>/dev/null; then
    echo ""
    echo "⚠️  需要先登录 ghcr.io 才能拉取镜像"
    echo ""
    echo "步骤："
    echo "  1. 访问 https://github.com/settings/tokens"
    echo "  2. 创建 Classic Token，权限勾选 read:packages"
    echo "  3. 运行以下命令登录："
    echo "     echo '你的_TOKEN' | docker login ghcr.io -u 你的GitHub用户名 --password-stdin"
    echo ""
    read -rp "登录完成后按 Enter 继续..."
fi

# ---------- 获取 compose 部署路径 ----------
read -rp "请输入 docker-compose.yml 所在目录路径（默认: $(pwd)）: " COMPOSE_DIR
COMPOSE_DIR="${COMPOSE_DIR:-$(pwd)}"

if [ ! -f "$COMPOSE_DIR/docker-compose.yml" ]; then
    echo "⚠️  未找到 docker-compose.yml，将在 $COMPOSE_DIR 创建一份"
    mkdir -p "$COMPOSE_DIR"
    cat > "$COMPOSE_DIR/docker-compose.yml" << EOF
services:
  toolkit:
    image: $IMAGE
    container_name: agent_tools_kit
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - TOOLKIT_DB=/app/data/toolkit.db
    restart: unless-stopped
EOF
    echo "✅ docker-compose.yml 已创建"
fi

# ---------- 先启动一次容器 ----------
echo ""
echo "🚀 首次启动容器..."
cd "$COMPOSE_DIR" && docker compose up -d
echo "✅ 容器已启动"

# ---------- 启动 Watchtower ----------
echo ""
echo "🛰️  启动 Watchtower 自动更新容器..."
echo "   - 检测间隔: 300 秒（5 分钟）"
echo "   - 自动清理旧镜像"

docker run -d \
    --name watchtower \
    --restart unless-stopped \
    -v /var/run/docker.sock:/var/run/docker.sock \
    ghcr.io/containrrr/watchtower:latest \
    --interval 300 \
    --cleanup \
    agent_tools_kit

echo ""
echo "✅ Watchtower 已启动！"
echo ""
echo "📋 查看日志: docker logs -f watchtower"
echo "⏹  停止自动更新: docker stop watchtower && docker rm watchtower"
echo "🔁 手动更新: docker compose -f $COMPOSE_DIR/docker-compose.yml pull && docker compose -f $COMPOSE_DIR/docker-compose.yml up -d"
