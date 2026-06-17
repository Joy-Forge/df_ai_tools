# 常见问题

## 启动

### 端口 8000 被占用

修改映射端口：`docker run -p 9000:8000 ...`，或修 `docker-compose.yml`。

### `docker compose` 与 `docker-compose` 区别

新版 Docker 自带 v2 插件 `docker compose`（带空格）。老系统才有 `docker-compose`（带连字符）。

## 接入 Agent

### Agent 看不到工具

1. 确认 `/api/health` 返回 ok
2. 确认 `/mcp` 端点可访问：`curl -I http://localhost:8000/mcp` 应返回 200 / SSE 头
3. 确认配置里 `url` / `cwd` 路径正确，Agent 进程能访问到

### SSE 一直断连

Nginx / 反代默认会缓冲 SSE 响应，必须 `proxy_buffering off`（见 [Deployment](Deployment)）。

## 数据

### 数据怎么迁移到新机器

1. 旧机器：`docker compose stop` → 复制 `./data/toolkit.db` 到新机器
2. 新机器：把文件放到 `./data/toolkit.db` → `docker compose up -d`

### 时区不对导致事件错位

容器默认 UTC。设 `TZ=Asia/Shanghai` 重建容器（见 [Deployment](Deployment)）。

### 怎么重置所有数据

`docker compose down` → `rm -rf ./data` → `docker compose up -d`。

## MCP 工具

### 一次能发多少条消息

单次 MCP 调用 = 一次函数调用，没硬上限。批量操作建议让 Agent 在循环里调用 5–10 个 / 批。

### 怎么限制 Agent 只能查不能改

当前没有基于角色的工具过滤。所有工具对所有连接的 Agent 可见。临时方案：单独部署一个只读实例（去掉 `add_*` / `update_*` / `delete_*` 工具 —— 需自行 fork）。

## 性能

### 单实例能撑多少用户

SQLite 写并发有限，**典型场景：1–10 个 Agent + 1 个用户的数据量**无压力。
>10 个并发写入或 > 100k 行记录时建议迁 Postgres（见 [Deployment](Deployment)）。

## 安全

### API Key 应该怎么生成

```bash
openssl rand -hex 32
```

长度 ≥ 32 字节随机串即可。不要用字典词、生日等。

### Webhook URL 会不会泄露

参见 [Notify 模块文档](Notify#安全注意)。建议：

- 启用 `API_KEY`
- 不要把 `.env` 提交到 git
- 在反代 / WAF 层限制 `/api/notify/*` 来源 IP

## TODO

- [ ] Agent 接入失败的诊断命令清单
- [ ] 已知 Agent（Claude Desktop / Cline / Continue）的兼容性问题
