# Agent Tools Kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/Joy-Forge/df_ai_tools/ci.yml?branch=main&label=CI)](https://github.com/Joy-Forge/df_ai_tools/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Joy-Forge/df_ai_tools?label=Release)](https://github.com/Joy-Forge/df_ai_tools/releases)
[![Docker Pulls](https://img.shields.io/docker/pulls/joy-forge/df_ai_tools?label=Docker%20Pulls)](https://github.com/Joy-Forge/df_ai_tools/pkgs/container/df_ai_tools)
[![Image Size](https://img.shields.io/docker/image-size/joy-forge/df_ai_tools/latest?label=Image%20Size)](https://github.com/Joy-Forge/df_ai_tools/pkgs/container/df_ai_tools)

把 **记账 / 待办 / 日历 / 通知** 4 个轻量服务合并为一个 API，**让 AI Agent 通过 MCP 协议（或 REST）直接读写你的数据**。
纯本地、SQLite、单镜像，开箱即用。

> 文档分层：**README** = 5 分钟跑起来 · **[Wiki](https://github.com/Joy-Forge/df_ai_tools/wiki)** = 模块手册与运维指南 · **[docs/](docs/)** = 开发者向深度文档

---

## 🚀 快速开始

**前提**：只需 [Docker](https://docs.docker.com/get-docker/)，无需 Python / Node。

### 一条命令（推荐路径）

> ⚠️ 数据存于容器内部，容器删除即丢。需要持久化或自动重启请跳到 [Wiki: 部署与运维](https://github.com/Joy-Forge/df_ai_tools/wiki/Deployment)。

```bash
# 🇨🇳 国内（阿里云）
docker run -d -p 8000:8000 crpi-1bkinvfgt16i5pgx.cn-shenzhen.personal.cr.aliyuncs.com/deerfish/ai_tools:latest

# 🌐 海外（GHCR）
docker run -d -p 8000:8000 ghcr.io/joy-forge/df_ai_tools:latest
```

> 完整说明：持久化卷、自动重启、Compose、反向代理、HTTPS、备份、API Key 鉴权 —
> **[Wiki › 部署与运维](https://github.com/Joy-Forge/df_ai_tools/wiki/Deployment)**
> 镜像源对比、参数表、`docker compose` 模板 —— **[Wiki › Deployment#镜像与启动方式](https://github.com/Joy-Forge/df_ai_tools/wiki/Deployment#镜像与启动方式)**

### ✅ 验证

```bash
curl http://localhost:8000/api/health
# → {"status":"ok"}
```

---

## 🤖 连接你的 Agent

启动后，Agent 可通过 MCP 协议自动发现 **19 个工具**（4 个模块）。

> 协议：MCP **Streamable HTTP**（2025-06-18 协议规范，默认传输；Claude Desktop / picoclaw / hermes 等现代客户端默认连这个）。

### SSE（Streamable HTTP，推荐）

```json
{
  "mcpServers": {
    "agent-tools-kit": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

> Agent 在其他机器 / NAS 上运行时，把 `localhost` 换成服务器 IP。

### stdio（不启 HTTP）

> Windows 用户注意：`cwd` 用正斜杠或转义反斜杠，例如 `E:/sync/agentscode/agent_tools_kit`。

```json
{
  "mcpServers": {
    "agent-tools-kit": {
      "command": "python",
      "args": ["-m", "src.mcp_entry"],
      "cwd": "E:/sync/agentscode/agent_tools_kit"
    }
  }
}
```

### 工具一览

| 模块 | 工具 |
|------|------|
| **记账** | `add_record` · `get_records` · `get_summary` · `update_record` · `delete_record` |
| **待办** | `add_todo` · `list_todos` · `mark_done` · `mark_undo` · `edit_todo` · `delete_todo` |
| **日历** | `add_event` · `list_events` · `get_pending_reminders` · `delete_event` |
| **通知** | `save_webhook` · `list_webhooks` · `send_notification` · `get_notify_log` |

> 各工具的字段、返回结构、典型用法见 **[Wiki: 模块手册](https://github.com/Joy-Forge/df_ai_tools/wiki)**。
> REST API 文档自动生成于 `http://localhost:8000/docs`。

---

## 🖥️ 命令行工具 (`aitools`)

通过 `aitools` CLI 在同一终端直接管理数据，适合快速操作和脚本自动化。

### 安装

```bash
pip install -e .                     # 从项目根目录安装
aitools --help                       # 验证
```

### 命令一览

| 命令 | 子命令 | 说明 |
|------|--------|------|
| `aitools todo` | `list` · `add` · `done` · `undo` · `edit` · `delete` | 管理待办事项 |
| `aitools accounting` | `list` · `add` · `summary` · `update` · `delete` | 管理记账记录 |
| `aitools calendar` | `list` · `add` · `delete` · `pending-reminders` · `reminders-log` | 管理日程事件 |
| `aitools notify` | `webhook-save` · `webhook-list` · `send` · `log` | 管理通知 |
| `aitools health` | — | 检查服务健康状态 |

### 常用示例

```bash
# 确认服务运行
aitools health

# 待办：添加 → 查看 → 标记完成
aitools todo add "买牛奶" --priority 2 --due "2026-06-20"
aitools todo list
aitools todo done 1

# 记账：记录支出 → 查看汇总
aitools accounting add 25.50 --category 餐饮 --note "午餐"
aitools accounting summary

# 日历：添加重复日程 → 查看未来事件
aitools calendar add --title "站会" --event-time "2026-06-20T09:00:00+08:00" --repeat daily
aitools calendar list --days 7

# 通知：保存 Webhook → 发送通知
aitools notify webhook-save --name my_hook --url "https://hooks.example.com/notify"
aitools notify send --channel webhook --target my_hook --title "提醒" --body "到时间了"
```

### 全局选项

| 选项 | 环境变量 | 说明 |
|------|----------|------|
| `--server URL` | `AITOOLS_SERVER` | 服务地址（默认 `http://127.0.0.1:8000`） |
| `--api-key KEY` | `AITOOLS_API_KEY` | API Key（服务启用鉴权时必填） |
| `--user USER` | `AITOOLS_USER` | 用户标识（默认 `default`） |

> 传递负数金额时需用 `--` 分隔，例如：`aitools accounting add -- -10.00 --category 退款`

### curl 速测

```bash
curl -X POST http://localhost:8000/api/accounting/add \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","amount":-42.5,"category":"餐饮","note":"午饭"}'

curl "http://localhost:8000/api/todo/list?user_id=test"
```

---

## 📁 数据 & 配置

- 数据落盘：`./data/toolkit.db`（SQLite），用 [DB Browser](https://sqlitebrowser.org/) 可直接打开
- 重置数据：删除该文件即可

| 变量 | 说明 | 默认 |
|------|------|------|
| `TOOLKIT_DB` | SQLite 文件路径 | `data/toolkit.db` |
| `API_KEY` | 启用后需 `X-API-Key` Header 鉴权 | 空（不鉴权） |

`.env` 示例（已 `.gitignore`）：

```ini
TOOLKIT_DB=data/toolkit.db
API_KEY=
```

---

## 🛠️ 本地开发

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
python -m pytest tests/ -v
```

或一键脚本（Linux / WSL / Windows PowerShell）：

```bash
./scripts/linux/run-local.sh       # 或 .\scripts\windows\run-local.ps1
```

VS Code 里按 `F5` 可选：Dev Server · Run All Tests · Docker Build & Run · Release。
完整工作流见 [docs/development-workflow.md](docs/development-workflow.md)。

## 🔄 CI/CD

| Workflow | 触发 | 功能 |
|----------|------|------|
| `ci.yml` | push / PR → main | 3 个 Python 版本跑测试 |
| `docker.yml` | push main / tag v\* | 构建并推送 ghcr.io 镜像 |
| `release.yml` | push tag v\* | 生成 Changelog + GitHub Release |

```bash
python scripts/release.py   # 一键：测试 → 构建 → 推送 → 发版
```

## 📖 延伸阅读

- **[Wiki 首页](https://github.com/Joy-Forge/df_ai_tools/wiki)** — 4 个模块的手册、运维指南、FAQ
- [docs/development-workflow.md](docs/development-workflow.md) — Issue → PR → 发布全流程
- [scripts/README.md](scripts/README.md) — 脚本说明
- [LICENSE](LICENSE) — MIT

## License

[MIT](LICENSE) © 2026 Joy-Forge
