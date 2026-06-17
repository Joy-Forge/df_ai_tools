# Agent Tools Kit

4 个轻量工具服务（**记账、待办、日历、通知**），合并为一个 API，供 AI Agent 通过 **MCP 协议** 或 **REST API** 调用。

---

## 🚀 快速开始（一条命令启动）

> **前提条件：只需安装 [Docker](https://docs.docker.com/get-docker/)**，无需 Python / Node 等任何开发环境。

### 🥇 极简版 — 一条命令直接跑

```bash
docker run -d -p 8000:8000 ghcr.io/joy-forge/df_ai_tools:latest
```

复制粘贴到终端，回车，完事。浏览器打开 `http://localhost:8000/api/health` 看到 `{"status":"ok"}` 即启动成功。

> ⚠️ 极简版数据存储在容器内部，容器删除后数据会丢失。如需持久化请用下面的推荐版。

---

### 🥈 生产推荐版（数据持久化 + 自动重启）

```bash
docker run -d \
  --name agent_tools_kit \
  -p 8000:8000 \
  -v ./data:/app/data \
  -e TOOLKIT_DB=/app/data/toolkit.db \
  --restart unless-stopped \
  ghcr.io/joy-forge/df_ai_tools:latest
```

与极简版的区别：

| 参数 | 作用 |
|------|------|
| `--name` | 容器命名，方便管理 |
| `-v ./data:/app/data` | 数据持久化到本地文件夹 |
| `-e TOOLKIT_DB=...` | 数据库路径指向持久化卷 |
| `--restart unless-stopped` | 系统重启 / 崩溃后自动拉起 |

---

### 🥉 Docker Compose

复制下面的内容保存为 `docker-compose.yml`，然后一条命令启动：

```yaml
services:
  toolkit:
    image: ghcr.io/joy-forge/df_ai_tools:latest
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
# 启动（自动拉取镜像）
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

---

## ✅ 验证服务

浏览器打开或执行：

```
http://localhost:8000/api/health
```

返回 `{"status": "ok"}` 即表示启动成功。

---

## 🤖 连接你的 Agent

服务启动后，Agent 可通过 **MCP 协议** 自动发现全部 **19 个工具**。

### 方式 1：SSE（推荐，最简配置）

在 Agent 配置中添加：

```json
{
  "mcpServers": {
    "agent-tools-kit": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

> 如果 Agent 在其他机器/NAS 上运行，把 `localhost` 换成服务器的 IP 地址。

### 方式 2：stdio（无需启动 HTTP 服务）

```json
{
  "mcpServers": {
    "agent-tools-kit": {
      "command": "python",
      "args": ["-m", "src.mcp_entry"],
      "cwd": "/path/to/agent-tools-kit"
    }
  }
}
```

### 可用 MCP 工具一览

| 模块 | 工具 | 说明 |
|------|------|------|
| **记账** | `add_record` / `get_records` / `get_summary` / `update_record` / `delete_record` | 记一笔、查账、统计 |
| **待办** | `add_todo` / `list_todos` / `mark_done` / `mark_undo` / `edit_todo` / `delete_todo` | 任务管理 |
| **日历** | `add_event` / `list_events` / `get_pending_reminders` / `delete_event` | 日程管理 |
| **通知** | `save_webhook` / `list_webhooks` / `send_notification` / `get_notify_log` | 消息推送 |

> Agent 连接后会自动列出这些工具，你也可以打开 `http://localhost:8000/docs` 查看 REST API 文档。

### 用 curl 快速测试

```bash
# 健康检查
curl http://localhost:8000/api/health

# 记一笔账
curl -X POST http://localhost:8000/api/accounting/add \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "amount": 42.5, "type": "expense", "category": "餐饮", "note": "午饭"}'

# 查待办
curl http://localhost:8000/api/todo/list?user_id=test

# 看 API 文档（浏览器打开）
# http://localhost:8000/docs
```

---

## 📁 数据

所有数据存储在项目根目录的 `./data/toolkit.db`（SQLite），可用 [DB Browser](https://sqlitebrowser.org/) 直接打开查看。

删除该文件即重置所有数据。

---

## ⚙️ 配置

### 方式 1：系统环境变量

直接设置系统环境变量即可覆盖默认值：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `TOOLKIT_DB` | SQLite 数据库文件路径（相对或绝对路径） | `data/toolkit.db` |
| `API_KEY` | API 访问密钥（可选；设置后需在 Header 中传 `X-API-Key`） | 空（不鉴权） |

**Linux / macOS：**
```bash
export TOOLKIT_DB=/path/to/custom.db
export API_KEY=your-secret-key
```

**Windows PowerShell：**
```powershell
$env:TOOLKIT_DB = "D:\data\my-toolkit.db"
$env:API_KEY = "your-secret-key"
```

### 方式 2：`.env` 文件（推荐本地开发）

复制示例文件并编辑：

```bash
# Linux / macOS
cp .env.example .env

# Windows
copy .env.example .env
```

`.env` 文件内容：

```ini
# 数据库路径（支持相对路径和绝对路径）
TOOLKIT_DB=data/toolkit.db

# API 密钥（留空则不启用鉴权）
API_KEY=
```

> ⚠️ `.env` 文件包含敏感信息，已加入 `.gitignore`，**不要提交到版本控制**。

---

---

> **以下是进阶内容**，面向**开发者和进阶用户**，普通使用者可跳过。

---

## 🔧 本地运行（无需 Docker）

```bash
# Linux / macOS
chmod +x scripts/linux/run-local.sh
./scripts/linux/run-local.sh

# Windows PowerShell
.\scripts\windows\run-local.ps1
```

脚本自动安装依赖 → 启动热重载开发服务器。

---

## 🛠️ 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动热重载服务
uvicorn src.main:app --reload --port 8000

# 运行测试
python -m pytest tests/ -v

# 代码检查（可选）
pip install pre-commit
pre-commit install && pre-commit run --all-files
```

### 一键启动（VS Code）

在 VS Code 中按 `F5` 或 `Ctrl+Shift+D` 打开运行面板，选择：

| 配置 | 用途 |
|------|------|
| `1. FastAPI Dev Server (热重载)` | 启动开发服务器 |
| `2. Run All Tests` | 运行全部测试 |
| `3. Docker: Build & Run` | Docker 方式启动 |
| `4. Release (打标签发布)` | 打 tag 并推送触发 CI |

> 📖 完整的开发工作流（Issue → 分支 → PR → 合并 → 发布）见 [docs/development-workflow.md](docs/development-workflow.md)

---

## 🔄 CI/CD

| Workflow | 触发条件 | 功能 |
|---------|---------|------|
| `ci.yml` | push / PR → main | 3 个 Python 版本运行测试 |
| `docker.yml` | push main / tag v\* | 构建 Docker 镜像 → 推送 ghcr.io |
| `release.yml` | push tag v\* | 生成 Changelog → 创建 GitHub Release |

发布流程：

```bash
# 一键发布（输入版本号，自动打 tag 并推送）
python scripts/release.py
# → 自动：测试 → 构建镜像 → 推送 GHCR → 创建 Release
```

---

## 📂 项目结构

```
agent-tools-kit/
├── src/                    # 源码
│   ├── main.py             # FastAPI 入口 + MCP SSE 端点
│   ├── mcp_entry.py        # MCP stdio 入口
│   ├── db.py               # 共享数据库
│   ├── accounting/         # 记账模块
│   ├── todo/               # 待办模块
│   ├── calendar/           # 日历模块
│   └── notify/             # 通知模块
├── scripts/
│   ├── linux/              # Linux 脚本
│   │   └── run-local.sh    #   本地 Python 启动
│   ├── windows/            # Windows 脚本
│   │   └── run-local.ps1
│   └── release.py          # 一键发布助手
├── tests/                  # 测试用例
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
