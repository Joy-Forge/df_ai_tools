"""一键接口测试脚本 — 启动服务 → 跑所有 REST 接口 → 关闭服务。

用法:
    python scripts/test_api_combo.py
    或在 VS Code 中选择 "🚀 启动服务 + 跑接口脚本"

功能:
    1. 启动 uvicorn 服务（子进程）
    2. 轮询 /api/health 等待就绪
    3. 用 httpx 测试所有 REST 端点（状态码 + 响应结构）
    4. 输出汇总，关闭服务
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# Force UTF-8 output on Windows (PowerShell defaults to GBK)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE = "http://127.0.0.1:8000"
TIMEOUT = 10  # seconds to wait for server startup
USER_ID = f"combo_test_{int(time.time())}"

# Track results
passed = 0
failed = 0
errors = []


def test(name: str, method: str, path: str, expect_status: int = 200,
         json_body: dict | None = None, params: dict | None = None,
         timeout: int = 5):
    """Send one HTTP request and check the status code."""
    global passed, failed
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = httpx.get(url, params=params, timeout=timeout, follow_redirects=False)
        elif method == "POST":
            r = httpx.post(url, json=json_body, params=params, timeout=timeout, follow_redirects=False)
        elif method == "PUT":
            r = httpx.put(url, json=json_body, params=params, timeout=timeout, follow_redirects=False)
        elif method == "DELETE":
            r = httpx.delete(url, params=params, timeout=timeout, follow_redirects=False)
        else:
            raise ValueError(f"Unknown method: {method}")

        ok = r.status_code == expect_status
        icon = "✅" if ok else "❌"
        detail = "" if ok else f"  (响应: {r.text[:100]})"
        print(f"  {icon} [{method:6s}] {path}  =>  {r.status_code} (期望 {expect_status}){detail}")
        if ok:
            passed += 1
        else:
            failed += 1
            errors.append(f"{method} {path}: got {r.status_code}, expected {expect_status}")
        return r
    except Exception as e:
        print(f"  ❌ [{method:6s}] {path}  =>  异常: {e}")
        failed += 1
        errors.append(f"{method} {path}: {e}")
        return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def run_tests():
    global USER_ID

    print("\n" + "=" * 50)
    print(f" Agent Tools Kit — 接口测试 (Python)")
    print(f" UserId: {USER_ID}")
    print("=" * 50)

    # --- Health ---
    print("\n--- Health ---")
    test("健康检查", "GET", "/api/health")

    # --- Accounting ---
    print("\n--- Accounting ---")
    r = test("添加记录", "POST", "/api/accounting/add", 200,
             json_body={"user_id": USER_ID, "amount": 99.5, "category": "餐饮", "note": "接口测试"})
    rec_id = r.json().get("id") if r and r.status_code == 200 else None

    test("记录列表", "GET", "/api/accounting/list", 200,
         params={"user_id": USER_ID})
    test("收支摘要", "GET", "/api/accounting/summary", 200,
         params={"user_id": USER_ID})

    if rec_id:
        test("更新记录", "PUT", f"/api/accounting/update/{rec_id}", 200,
             json_body={"amount": 120, "note": "修改后"},
             params={"user_id": USER_ID})
    else:
        print("  ⚠️  跳过更新记录 (未获取到 ID)")

    # --- Todo ---
    print("\n--- Todo ---")
    r = test("添加待办", "POST", "/api/todo/add", 200,
             json_body={"user_id": USER_ID, "content": "接口测试任务", "priority": 2, "due_date": "2025-12-31"})
    todo_id = r.json().get("id") if r and r.status_code == 200 else None

    test("待办列表", "GET", "/api/todo/list", 200,
         params={"user_id": USER_ID})

    if todo_id:
        test("标记完成", "POST", f"/api/todo/done/{todo_id}", 200,
             params={"user_id": USER_ID})
        test("撤销完成", "POST", f"/api/todo/undo/{todo_id}", 200,
             params={"user_id": USER_ID})
        test("编辑待办", "PUT", f"/api/todo/edit/{todo_id}", 200,
             json_body={"content": "接口测试任务v2", "priority": 1},
             params={"user_id": USER_ID})
    else:
        print("  ⚠️  跳过 done/undo/edit (未获取到 ID)")

    # --- Calendar ---
    print("\n--- Calendar ---")
    future = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 7200))
    r = test("添加日程", "POST", "/api/calendar/add", 200,
             json_body={"user_id": USER_ID, "title": "接口测试会议",
                        "event_time": future, "remind_before": 15, "repeat": "none"})
    evt_id = r.json().get("id") if r and r.status_code == 200 else None

    test("日程列表", "GET", "/api/calendar/list", 200,
         params={"user_id": USER_ID, "days": 60})
    test("待触发提醒", "GET", "/api/calendar/pending_reminders", 200,
         params={"user_id": USER_ID})
    test("提醒日志", "GET", "/api/calendar/reminders_log", 200,
         params={"user_id": USER_ID})

    # --- Notify ---
    print("\n--- Notify ---")
    test("保存Webhook", "POST", "/api/notify/webhook/save", 200,
         json_body={"user_id": USER_ID, "name": "测试Hook",
                    "url": "https://httpbin.org/post", "method": "POST", "headers": "{}"})
    test("Webhook列表", "GET", "/api/notify/webhook/list", 200,
         params={"user_id": USER_ID})
    test("发送通知", "POST", "/api/notify/send", 200,
         json_body={"user_id": USER_ID, "channel": "webhook",
                    "target": "测试Hook", "title": "测试", "body": "接口测试消息"},
         timeout=15)
    test("通知日志", "GET", "/api/notify/log", 200,
         params={"user_id": USER_ID})

    # --- Backup ---
    print("\n--- Backup ---")
    test("创建备份", "POST", "/api/backup/create", 200)
    test("备份列表", "GET", "/api/backup/list", 200)

    # --- Data Exchange ---
    print("\n--- Data Exchange ---")
    test("JSON导出", "GET", f"/api/data/export/{USER_ID}", 200)
    test("CSV导出", "GET", f"/api/data/export/{USER_ID}/csv/accounting", 200)
    test("JSON导入", "POST", "/api/data/import", 200,
         json_body={"user_id": USER_ID,
                    "data": {"accounting": [{"amount": 50, "category": "交通", "note": "导入"}]}})

    # --- Audit ---
    print("\n--- Audit ---")
    test("审计日志", "GET", "/api/audit/log", 200,
         params={"user_id": USER_ID, "limit": 20})

    # --- MCP ---
    print("\n--- MCP ---")
    test("MCP端点(GET)", "GET", "/mcp", 307)

    # --- Summary ---
    print("\n" + "=" * 50)
    total = passed + failed
    print(f" 测试完成！通过: {passed}  |  失败: {failed}  |  总计: {total}")
    if failed == 0:
        print(" 🎉 全部通过！")
    else:
        print(" ⚠️  有以下异常:")
        for e in errors:
            print(f"   - {e}")
    print("=" * 50 + "\n")
    return failed == 0


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------
def wait_for_server(url: str, timeout: float) -> bool:
    """Poll the health endpoint until the server is ready."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{url}/api/health", timeout=2)
            if r.status_code == 200:
                return True
        except (httpx.ConnectError, httpx.ReadTimeout):
            pass
        time.sleep(0.3)
    return False


def main():
    print("🚀 启动服务...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(Path(__file__).parent.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )

    try:
        if not wait_for_server(BASE, TIMEOUT):
            print(f"❌ 服务未在 {TIMEOUT}s 内启动")
            proc.terminate()
            sys.exit(1)

        print("✅ 服务已就绪\n")
        success = run_tests()

        print("🛑 关闭服务...")
        proc.terminate()
        proc.wait(timeout=5)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n🛑 中断，关闭服务...")
        proc.terminate()
        proc.wait(timeout=5)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        proc.terminate()
        proc.wait(timeout=5)
        sys.exit(1)


if __name__ == "__main__":
    main()
