# 日历模块

> **4 个工具**：`add_event` / `list_events` / `get_pending_reminders` / `delete_event`

## 数据模型

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | 用户标识 |
| `title` | string | ✅ | 事件标题 |
| `event_time` | string | ✅ | ISO 时间 `YYYY-MM-DDTHH:MM:SS` |
| `remind_before` | int | ❌ | 提前多少分钟提醒，默认 10 |
| `repeat` | string | ❌ | `""` / `daily` / `weekly` / `monthly` |

## 工具一览

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `add_event` | 新建事件 | `user_id`, `title`, `event_time`, `remind_before=10`, `repeat=""` |
| `list_events` | 查未来 N 天 | `user_id`, `days=30`, `offset=0` |
| `get_pending_reminders` | 待提醒项 | `user_id` |
| `delete_event` | 删除 | `user_id`, `event_id` |

## curl 示例

```bash
# 新建一次事件，提前 15 分钟提醒
curl -X POST http://localhost:8000/api/calendar/add \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","title":"团队周会","event_time":"2026-06-20T10:00:00","remind_before":15}'

# 每周重复
curl -X POST http://localhost:8000/api/calendar/add \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","title":"周会","event_time":"2026-06-20T10:00:00","repeat":"weekly"}'

# 查未来 7 天
curl "http://localhost:8000/api/calendar/list?user_id=alice&days=7"

# 待提醒
curl "http://localhost:8000/api/calendar/reminders?user_id=alice"
```

## 时区

> ⚠️ **时区是本模块最容易踩的坑**。`event_time` 入参是**字面量时间**（不带时区），系统按**容器时区**解释。
>
> 部署时请确认：
> - 容器时区与用户所在地一致（启动时加 `-e TZ=Asia/Shanghai`），或
> - 始终用 UTC 入参，UI 侧再转本地

## 重复事件

`repeat` 当前实现为 **服务端展开**：每次 `list_events` 实际查询时会按规则生成多个 occurrence。
修改 `repeat` 需 `edit_event`（待补工具）。

## 错误情况

- `event_time` 解析失败 → 校验失败
- `remind_before` 负数 → 校验失败
- `repeat` 取值不在白名单 → 校验失败

## TODO

- [ ] `edit_event` 工具（当前模块只有 add / list / delete）
- [ ] `get_pending_reminders` 触发通知的机制（轮询？事件回调？需查 service 实现）
- [ ] 重复事件的"修改单个 occurrence"语义
