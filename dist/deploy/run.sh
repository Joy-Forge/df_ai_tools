#!/bin/bash
# 生产环境 Docker 启动脚本（Linux）
cd "$(dirname "$0")" && docker compose pull && docker compose up -d
