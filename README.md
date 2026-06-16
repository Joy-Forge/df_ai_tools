# Agent Tools Kit

4 个轻量工具服务，合并为一个 API，供 Agent 通过 **REST API** 或 **MCP 协议**调用：记账、Todo、日历提醒、通知桥接。

## 快速开始

### 方式 A：Docker 部署（推荐）

适合 NAS / VPS 等长期运行场景。

```bash
chmod +x docker-run.sh
./docker-run.sh
```

或手动：
```bash
docker compose up -d --build
```

### 方式 B：本地 Python 运行

适合开发调试，不需要 Docker，有 Python 3.10+ 就行。

```bash
chmod +x run.sh
./run.sh
```

或手动：
```bash
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### 验证

服务启动后访问 `http://localhost:8000/api/health`，返回 `{"status": "ok"}` 即表示成功。

## REST API

| 模块 | 端点 | 说明 |
|------|------|------|
| **记账** | `POST /api/accounting/add` | 添加收支记录 |
| | `GET /api/accounting/list?user_id=` | 查询记录 |
| | `GET /api/accounting/summary?user_id=` | 汇总统计 |
| | `DELETE /api/accounting/delete/{id}?user_id=` | 删除记录 |
| **待办** | `POST /api/todo/add` | 添加待办 |
| | `GET /api/todo/list?user_id=` | 查询待办列表 |
| | `POST /api/todo/done/{id}?user_id=` | 标记完成 |
| | `POST /api/todo/undo/{id}?user_id=` | 恢复未完成 |
| | `DELETE /api/todo/delete/{id}?user_id=` | 删除待办 |
| **日历** | `POST /api/calendar/add` | 添加日程事件 |
| | `GET /api/calendar/list?user_id=` | 查询日程 |
| | `DELETE /api/calendar/delete/{id}?user_id=` | 删除日程 |
| | `GET /api/calendar/pending_reminders?user_id=` | 待提醒事项 |
| **通知** | `POST /api/notify/webhook/save` | 保存 Webhook |
| | `GET /api/notify/webhook/list?user_id=` | Webhook 列表 |
| | `POST /api/notify/send` | 发送通知 |
| | `GET /api/notify/log?user_id=` | 发送记录 |

详细请求体格式见各模块 API 文档（`/docs`）。

## MCP 协议（Agent 调用）

Agent 通过 MCP 协议连接后，自动发现全部 **16 个工具**。

### 方式 1：SSE（推荐）

Agent 配置指向 SSE 端点：

```json
{
  "mcpServers": {
    "agent-tools-kit": {
      "url": "http://your-nas-ip:8000/mcp"
    }
  }
}
```

### 方式 2：stdio

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

### 可用 MCP 工具

| 模块 | 工具 | 说明 |
|------|------|------|
| 记账 | `add_record` | 记账 |
| | `get_records` | 查询记录 |
| | `get_summary` | 汇总统计 |
| | `delete_record` | 删除记录 |
| 待办 | `add_todo` | 添加待办 |
| | `list_todos` | 查询待办列表 |
| | `mark_done` | 标记完成 |
| | `delete_todo` | 删除待办 |
| 日历 | `add_event` | 添加日程 |
| | `list_events` | 查询日程 |
| | `get_pending_reminders` | 待提醒事项 |
| | `delete_event` | 删除日程 |
| 通知 | `save_webhook` | 保存 Webhook |
| | `list_webhooks` | Webhook 列表 |
| | `send_notification` | 发送通知 |
| | `get_notify_log` | 发送记录 |

## 开发 & 测试

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（热重载）
uvicorn src.main:app --reload --port 8000

# 访问 API 文档
open http://localhost:8000/docs

# 运行测试
python -m pytest tests/ -v
```

## 数据

所有数据存储在 `./data/toolkit.db`（SQLite），可直接用 DB Browser 打开查看。

## 部署到 NAS/VPS

### Docker 方式（推荐）

1. 将整个文件夹上传到 NAS/VPS
2. 运行 `./docker-run.sh` 或 `docker compose up -d --build`
3. 数据通过 volume 映射持久化到 `./data/`

### 本地 Python 方式

如果 NAS 上已安装 Python 3.10+，不想用 Docker：

```bash
# 安装依赖
pip install -r requirements.txt

# 后台启动（用 nohup 或 tmux/screen）
nohup uvicorn src.main:app --host 0.0.0.0 --port 8000 > toolkit.log 2>&1 &
```

## 提醒推送

日历服务每分钟自动检查到期提醒（通过 APScheduler）。提醒仅记录到日志，如需推送到手机：

1. 在通知服务中配置 Webhook（如 Bark、Server 酱、企业微信机器人）
2. Agent 可通过 `send_notification` 工具发送推送
3. 或由 Agent 轮询 `get_pending_reminders` 触发推送

## 项目结构

```
agent-tools-kit/
├── src/
│   ├── main.py                 # FastAPI 入口 + MCP 端点
│   ├── db.py                   # 共享数据库模块（合并 DB）
│   ├── mcp_entry.py            # 独立 MCP stdio 入口
│   ├── accounting/
│   │   ├── router.py           # REST API 路由
│   │   └── tools.py            # MCP 工具定义
│   ├── todo/
│   │   ├── router.py
│   │   └── tools.py
│   ├── calendar/
│   │   ├── router.py
│   │   └── tools.py
│   └── notify/
│       ├── router.py
│       └── tools.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── docker-run.sh          # Docker 一键启动
└── run.sh                 # 本地 Python 一键启动
```
