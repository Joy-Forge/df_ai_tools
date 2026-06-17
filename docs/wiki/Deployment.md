# 部署与运维

> 多种启动方式、备份、迁移、鉴权、时区。

## 镜像与启动方式

镜像托管在两处，按需选择：

| 镜像源 | 地址 | 何时选 |
|--------|------|--------|
| 🇨🇳 阿里云 ACR | `crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ai_tools:latest` | **国内用户推荐**（访问快） |
| 🌐 GitHub Container Registry | `ghcr.io/joy-forge/df_ai_tools:latest` | 海外 / 通用 |
| 本地构建 | `docker compose up -d --build` | 改源码后自测 |

> Docker 镜像名必须小写 —— `joy-forge` 即使 GitHub 用户名是 `Joy-Forge`，包路径仍用小写。
>
> 本文档的示例命令默认用**阿里云**镜像；GHCR 只需把 `image` 字段替换为 `ghcr.io/joy-forge/df_ai_tools:latest` 即可。

### 方式 1：极简版（一条命令，零配置）

适合 **试玩 / 临时演示**。容器删除后数据丢失。

```bash
# 🇨🇳 阿里云
docker run -d -p 8000:8000 crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ai_tools:latest

# 🌐 GHCR
docker run -d -p 8000:8000 ghcr.io/joy-forge/df_ai_tools:latest
```

### 方式 2：生产推荐版（数据持久化 + 自动重启）

```bash
docker run -d --name agent_tools_kit \
  -p 8000:8000 \
  -v ./data:/app/data \
  -e TOOLKIT_DB=/app/data/toolkit.db \
  --restart unless-stopped \
  crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ai_tools:latest
```

| 参数 | 作用 |
|------|------|
| `--name` | 容器命名（便于 `docker logs agent_tools_kit`） |
| `-v ./data:/app/data` | 数据持久化到宿主机 |
| `-e TOOLKIT_DB=...` | 数据库指向持久化卷 |
| `--restart unless-stopped` | 崩溃 / 系统重启后自动拉起 |

### 方式 3：Docker Compose

```yaml
services:
  toolkit:
    image: crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ai_tools:latest
    container_name: agent_tools_kit
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - TOOLKIT_DB=/app/data/toolkit.db
    restart: unless-stopped
```

```bash
# 拉取并启动
docker compose pull
docker compose up -d

# 本地源码构建
docker compose up -d --build

# 实时日志
docker compose logs -f

# 停止并保留数据卷
docker compose down

# 停止并删除数据卷（**慎用**，会清空数据库）
docker compose down -v
```

### 方式 4：本地 Python（开发模式）

热重载，适合改源码：

```bash
# Linux / WSL
chmod +x scripts/linux/run-local.sh
./scripts/linux/run-local.sh

# Windows PowerShell
.\scripts\windows\run-local.ps1
```

或手动：

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### 启动后验证

```bash
curl http://localhost:8000/api/health
# → {"status":"ok"}
```

---

## 启用 API Key 鉴权

```bash
docker run -d ... \
  -e API_KEY=your-strong-random-string \
  -e TOOLKIT_DB=/app/data/toolkit.db
```

调用时：

```bash
curl http://localhost:8000/api/health \
  -H "X-API-Key: your-strong-random-string"
```

## 数据备份

```bash
# 简单 cp（注意一致性：先停容器，或使用 SQLite 在线备份 API）
docker compose stop
cp ./data/toolkit.db ./backup/toolkit-$(date +%F).db
docker compose start
```

更好的做法：调用 `sqlite3 .backup`（需在容器内执行）：

```bash
docker exec agent_tools_kit \
  sqlite3 /app/data/toolkit.db ".backup '/app/data/backup.db'"
docker cp agent_tools_kit:/app/data/backup.db ./backup/
```

## 迁移到 PostgreSQL

> ⚠️ **当前实现是 SQLite-only**。PostgreSQL 支持是规划中，需在 service 层加适配。
>
> 不在 v1 范围内，但保留扩展点。

## 时区设置

容器默认 UTC，部署在非 UTC 时区下请显式指定：

```yaml
services:
  toolkit:
    image: ...
    environment:
      - TZ=Asia/Shanghai
    volumes: ["/etc/localtime:/etc/localtime:ro"]
```

## 日志

```bash
docker compose logs -f            # 实时
docker compose logs --tail=200    # 最近 200 行
```
