# Agent Tools Kit

4 个轻量工具服务（**记账、待办、日历、通知**），合并为一个 API，供 AI Agent 通过 **MCP 协议** 或 **REST API** 调用。

---

## 🚀 快速开始

> **选择一条路走通即可，推荐 Docker。**

### 前置条件

| 方式 | 要求 |
|------|------|
| **Docker（推荐）** | 安装 [Docker](https://docs.docker.com/get-docker/) |
| **本地 Python** | Python 3.10+ |

---

### 方式 A：Docker（推荐，一行启动）

```bash
# Linux / macOS
chmod +x scripts/linux/run-docker.sh
./scripts/linux/run-docker.sh

# Windows PowerShell
.\scripts\windows\run-docker.ps1
```

脚本会自动构建镜像 → 启动容器 → 在 `8000` 端口提供服务。

查看日志：`docker compose logs -f`
停止服务：`docker compose down`

---

### 方式 B：本地 Python（不需要 Docker）

```bash
# Linux / macOS
chmod +x scripts/linux/run-local.sh
./scripts/linux/run-local.sh

# Windows PowerShell
.\scripts\windows\run-local.ps1
```

脚本自动安装依赖 → 启动热重载开发服务器。

---

### ✅ 验证服务

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

---

> **以下是进阶内容**，新手可以先跳过，等跑通上面 MVP 流程后再看。

---

## ⚙️ 生产部署

### 从 GHCR 拉取预构建镜像（无需本地构建）

项目在 GitHub 推送 tag 时自动构建镜像并推送到 `ghcr.io`。在服务器上：

```bash
# 1. 登录 ghcr.io（需要 GitHub Personal Access Token）
echo '你的_TOKEN' | docker login ghcr.io -u 你的用户名 --password-stdin

# 2. 生成部署包（会自动填入正确的镜像地址）
python scripts/deploy/generate-deploy.py

# 3. 进入生成目录并启动
cd dist/deploy
docker compose up -d
```

> 也可以直接到 GitHub Releases 页面下载 `*-deploy.tar.gz`，解压后运行 `./run.sh`。

### 自动更新（Watchtower）

在 NAS/VPS 上启动 Watchtower 后，它会每 5 分钟检查 GHCR 上的新镜像，自动拉取并重启容器：

```bash
# Linux
./scripts/linux/setup-watchtower.sh

# Windows
.\scripts\windows\setup-watchtower.ps1
```

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
| `4. Generate Deploy Package` | 生成部署包 |

---

## 🔄 CI/CD

| Workflow | 触发条件 | 功能 |
|---------|---------|------|
| `ci.yml` | push / PR → main | 3 个 Python 版本运行测试 |
| `docker.yml` | push main / tag v\* | 构建 Docker 镜像 → 推送 ghcr.io |
| `release.yml` | push tag v\* | 生成 Changelog → 打包部署包 → 创建 Release |

发布流程：

```bash
git tag v1.0.0
git push origin v1.0.0
# → 自动：测试 → 构建镜像 → 推送 GHCR → Release
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
│   │   ├── run-local.sh    #   本地 Python 启动
│   │   └── run-docker.sh   #   Docker 启动
│   ├── windows/            # Windows 脚本
│   │   ├── run-local.ps1
│   │   └── run-docker.ps1
│   ├── deploy/             # 部署相关
│   │   ├── templates/      #   部署包模板
│   │   ├── generate-deploy.py  # 部署包生成器
│   │   ├── setup-watchtower.sh #   自动更新（Linux）
│   │   └── setup-watchtower.ps1 # 自动更新（Windows）
├── dist/deploy/            # 生成的部署包（运行 deploy/generate-deploy.py 后出现）
├── tests/                  # 测试用例
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
