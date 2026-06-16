# 脚本说明

## 快速索引

| 脚本 | 用途 | 前置条件 |
|------|------|---------|
| `linux/run-local.sh` | 本地 Python 启动 | Python 3.10+ |
| `linux/run-docker.sh` | Docker 方式启动 | Docker |
| `windows/run-local.ps1` | 本地 Python 启动 | Python 3.10+ |
| `windows/run-docker.ps1` | Docker 方式启动 | Docker Desktop |
| `deploy/setup-watchtower.sh` | 配置 Watchtower 自动更新（Linux） | Docker, GitHub PAT |
| `deploy/setup-watchtower.ps1` | 配置 Watchtower 自动更新（Windows） | Docker, GitHub PAT |
| `deploy/generate-deploy.py` | 生成 dist/deploy/ 部署包 | Python 3.10+, git |

## 使用示例

```bash
# Linux / macOS
./scripts/linux/run-local.sh
./scripts/linux/run-docker.sh
./scripts/deploy/setup-watchtower.sh

# Windows PowerShell
.\scripts\windows\run-local.ps1
.\scripts\windows\run-docker.ps1
.\scripts\deploy\setup-watchtower.ps1
```
