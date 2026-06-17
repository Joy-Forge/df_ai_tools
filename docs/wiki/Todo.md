# 待办模块

> **6 个工具**：`add_todo` / `list_todos` / `mark_done` / `mark_undo` / `edit_todo` / `delete_todo`

## 数据模型

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | 用户标识 |
| `content` | string | ✅ | 待办内容 |
| `priority` | int | ❌ | 1=高 / 2=中 / 3=低，默认 1 |
| `due_date` | string | ❌ | 截止日期 `YYYY-MM-DD` |

## 状态机

```
[未完成] ──mark_done──▶ [已完成]
   ▲                       │
   └──────mark_undo────────┘
```

## 工具一览

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `add_todo` | 新增 | `user_id`, `content`, `priority?=1`, `due_date?=""` |
| `list_todos` | 列表 | `user_id`, `status="all"\|"pending"\|"done"`, `limit=30`, `offset=0` |
| `mark_done` | 标记完成 | `user_id`, `todo_id` |
| `mark_undo` | 恢复 | `user_id`, `todo_id` |
| `edit_todo` | 编辑 | `user_id`, `todo_id`, `content?`, `priority?`, `due_date?` |
| `delete_todo` | 删除 | `user_id`, `todo_id` |

## curl 示例

```bash
# 新增
curl -X POST http://localhost:8000/api/todo/add \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","content":"买菜","priority":2,"due_date":"2026-06-20"}'

# 查未完成
curl "http://localhost:8000/api/todo/list?user_id=alice&status=pending"

# 标记完成
curl -X POST http://localhost:8000/api/todo/done \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","todo_id":42}'
```

## MCP 调用示例

```
Agent: 提醒我明天下班前提交周报，优先级高
Tool:   add_todo(user_id="alice", content="提交周报", priority=1, due_date="2026-06-17")

Agent: 看一下我还有什么没做完的
Tool:   list_todos(user_id="alice", status="pending")
```

## 错误情况

- `due_date` 格式错 → 后端校验失败
- `todo_id` 不存在 / 用户不匹配 → `"待办不存在"`（与记账一致的安全语义）

## TODO

- [ ] `priority` 排序规则（list_todos 默认是否按优先级）
- [ ] 过期但未完成的待办是否有视觉标记
- [ ] 与日历模块的协作（截止日是否自动建事件）
