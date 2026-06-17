# 通知模块

> **4 个工具**：`save_webhook` / `list_webhooks` / `send_notification` / `get_notify_log`

## 数据模型（Webhook 配置）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | 用户标识 |
| `name` | string | ✅ | Webhook 标识（用于发送时定位） |
| `url` | string | ✅ | 目标 URL |
| `method` | string | ❌ | `POST` / `PUT`，默认 `POST` |
| `headers` | string | ❌ | JSON 字符串，默认 `"{}"` |

## 工具一览

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `save_webhook` | 保存 / 更新 Webhook | `user_id`, `name`, `url`, `method="POST"`, `headers="{}"` |
| `list_webhooks` | 列出已保存 | `user_id` |
| `send_notification` | **异步**发送 | `user_id`, `channel="webhook"`, `target=name`, `title`, `body` |
| `get_notify_log` | 发送历史 | `user_id`, `limit=20`, `offset=0` |

## curl 示例

```bash
# 保存一个飞书/钉钉/企业微信/Slack 等任意 webhook
curl -X POST http://localhost:8000/api/notify/webhook/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"alice",
    "name":"feishu-bot",
    "url":"https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    "method":"POST"
  }'

# 列出
curl "http://localhost:8000/api/notify/webhook/list?user_id=alice"

# 发送
curl -X POST http://localhost:8000/api/notify/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"alice",
    "channel":"webhook",
    "target":"feishu-bot",
    "title":"记账提醒",
    "body":"今天花了 38 元"
  }'

# 发送历史
curl "http://localhost:8000/api/notify/log?user_id=alice"
```

## MCP 调用示例

```
Agent: 以后所有"今天花了超过 100 块"都用飞书机器人通知我
Tool:   save_webhook(user_id="alice", name="feishu-bot",
                     url="https://open.feishu.cn/.../hook/xxx")
```

## 安全注意

> ⚠️ **不要把 Webhook URL 写到公开仓库**。`webhook.url` 和 `headers` 在 `get_notify_log` 中**默认不返回明文 URL**（需查实现确认）。
>
> 启用 `API_KEY` 鉴权后，未鉴权请求无法触发 send_notification。

## 错误情况

- `url` 不是合法 http(s) → 校验失败
- `headers` 不是合法 JSON 字符串 → 校验失败
- `target=name` 不存在 → 发送失败，写入 log
- 远端返回 4xx/5xx → log 记录 status_code

## TODO

- [ ] `headers` 中能否包含 `Authorization` 等敏感字段（生产是否需要加密存储）
- [ ] 重试机制（当前 send 失败是否重试）
- [ ] 与 `get_pending_reminders` 的联动：到期事件是否自动 send_notification
