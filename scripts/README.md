# 脚本说明

## 快速索引

| 脚本 | 用途 | 前置条件 |
|------|------|---------|
| `linux/run-local.sh` | 本地 Python 启动 | Python 3.10+ |
| `windows/run-local.ps1` | 本地 Python 启动 | Python 3.10+ |
| `release.py` | 一键打 tag 并推送发布 | git |

## Docker 方式启动（推荐）

直接用 `docker compose` 命令，无需脚本：

```bash
# 构建并启动（开发环境）
docker compose up -d --build

# 从 GHCR 拉取并启动（生产环境）
docker compose pull
docker compose up -d

# 停止
docker compose down
```
