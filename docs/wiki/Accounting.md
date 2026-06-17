# 记账模块

> **5 个工具**：`add_record` / `get_records` / `get_summary` / `update_record` / `delete_record`

## 数据模型

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | 用户标识，多用户隔离用 |
| `amount` | float | ✅ | 正数=收入，**负数=支出** |
| `category` | string | ✅ | 分类名，如 `餐饮` / `交通` / `工资` |
| `note` | string | ❌ | 备注 |

> 📌 **约定**：`amount` 正负号区分收支，而不是用 `type` 字段。这是当前实现，扩展模块时不要破坏。

## 工具一览

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `add_record` | 记一笔 | `user_id`, `amount`, `category`, `note?` |
| `get_records` | 查最近 N 条 | `user_id`, `limit=20`, `offset=0` |
| `get_summary` | 统计汇总 | `user_id` |
| `update_record` | 更新 | `user_id`, `record_id`, `amount?`, `category?`, `note?` |
| `delete_record` | 删除 | `user_id`, `record_id` |

## curl 示例

```bash
# 记一笔支出
curl -X POST http://localhost:8000/api/accounting/add \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","amount":-42.5,"category":"餐饮","note":"午饭"}'

# 记一笔收入
curl -X POST http://localhost:8000/api/accounting/add \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","amount":8000,"category":"工资","note":"6月"}'

# 查最近 10 条
curl "http://localhost:8000/api/accounting/list?user_id=alice&limit=10"

# 月度汇总
curl "http://localhost:8000/api/accounting/summary?user_id=alice"

# 更新
curl -X POST http://localhost:8000/api/accounting/update \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","record_id":123,"note":"修改后的备注"}'

# 删除
curl -X POST http://localhost:8000/api/accounting/delete \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","record_id":123}'
```

## MCP 调用示例

```
Agent: 帮我记一笔今天午饭 38 块
Tool:   add_record(user_id="alice", amount=-38, category="餐饮", note="午饭")
        → 已添加
```

## 错误情况

- `amount=0` → 业务校验失败（无意义）
- `record_id` 不存在 → `delete` / `update` 返回 `"记录不存在"`
- `user_id` 不匹配 → 视为无权限，返回相同 `"记录不存在"`（不暴露存在性）

## TODO（待补充）

- [ ] 返回结构示例（`get_records` 的 JSON 字段）
- [ ] 跨月查询的字段（当前是否支持 `from` / `to`）
- [ ] 分类字典（是否固定可枚举）
- [ ] 与 `get_summary` 输出的对齐说明
