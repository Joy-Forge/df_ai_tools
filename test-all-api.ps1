# ============================================================
# Agent Tools Kit — 全接口测试脚本 (PowerShell)
# 使用方法：先启动服务，然后在 PowerShell 中粘贴执行
# 服务默认地址: http://127.0.0.1:8000
# 如果设置了 API_KEY，修改下方 $ApiKey 变量
# ============================================================

$Base = "http://127.0.0.1:8000"
$ApiKey = ""   # 如果服务设置了 API_KEY，在这里填入
$UserId = "test_user_$(Get-Random -Maximum 99999)"
$Passed = 0
$Failed = 0
$Results = @()

function Test-Api {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Path,
        [object]$Body = $null,
        [int]$ExpectStatus = 200,
        [switch]$NoAuth
    )
    $url = "$Base$Path"
    $headers = @{}
    if (-not $NoAuth -and $ApiKey) {
        $headers["X-API-Key"] = $ApiKey
    }

    try {
        $params = @{
            Uri     = $url
            Method  = $Method
            Headers = $headers
            UseBasicParsing = $true
        }
        if ($Body -ne $null) {
            $json = $Body | ConvertTo-Json -Depth 10 -Compress
            $params["Body"] = $json
            $params["ContentType"] = "application/json"
        }

        $resp = Invoke-WebRequest @params -ErrorAction Stop
        $status = $resp.StatusCode
        try {
            $respBody = $resp.Content | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            Write-Host "   [DEBUG] JSON parse failed for $Method $Path" -ForegroundColor DarkYellow
            Write-Host "   [DEBUG] Raw content: $($resp.Content.Substring(0, [Math]::Min(200, $resp.Content.Length)))" -ForegroundColor DarkYellow
            $respBody = $null
        }
    }
    catch {
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
            $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
            $respBody = $reader.ReadToEnd() | ConvertFrom-Json -ErrorAction SilentlyContinue
            $reader.Close()
        }
        else {
            $status = -1
            $respBody = $null
            Write-Host "   [DEBUG] Exception: $($_.Exception.Message)" -ForegroundColor DarkYellow
        }
    }

    $ok = $status -eq $ExpectStatus
    if ($ok) { $script:Passed++ } else { $script:Failed++ }

    $icon = if ($ok) { "✅" } else { "❌" }
    $msg = "$icon [$Method] $Path  =>  $status (期望 $ExpectStatus)"
    Write-Host $msg -ForegroundColor $(if ($ok) { "Green" } else { "Red" })
    if (-not $ok) {
        Write-Host "   响应: $($respBody | ConvertTo-Json -Depth 5 -Compress)" -ForegroundColor Yellow
    }

    $script:Results += [PSCustomObject]@{
        Name   = $Name
        Method = $Method
        Path   = $Path
        Status = $status
        OK     = $ok
    }

    return $respBody
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Agent Tools Kit — 全接口测试" -ForegroundColor Cyan
Write-Host " UserId: $UserId" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------
# 1. Health
# --------------------------------------------------
Write-Host "--- Health ---" -ForegroundColor Magenta
Test-Api "健康检查" "GET" "/api/health" -NoAuth
Write-Host ""

# --------------------------------------------------
# 2. Auth
# --------------------------------------------------
Write-Host "--- Auth ---" -ForegroundColor Magenta
# Auth register/login/users 已跳过（agent 工具不需要用户登录）
Write-Host ""

# --------------------------------------------------
# 3. Accounting
# --------------------------------------------------
Write-Host "--- Accounting ---" -ForegroundColor Magenta
$recBody = @{ user_id = $UserId; amount = 99.5; category = "餐饮"; note = "午餐测试" }
$rec = Test-Api "添加记录" "POST" "/api/accounting/add" -Body $recBody
$recId = $rec.id

Test-Api "记录列表" "GET" "/api/accounting/list?user_id=$UserId"
Test-Api "收支摘要" "GET" "/api/accounting/summary?user_id=$UserId"

$updateBody = @{ amount = 120; note = "修改后" }
Test-Api "更新记录" "PUT" "/api/accounting/update/$($recId)?user_id=$UserId" -Body $updateBody
#Test-Api "删除记录" "DELETE" "/api/accounting/delete/$($recId)?user_id=$UserId"
Write-Host ""

# --------------------------------------------------
# 4. Todo
# --------------------------------------------------
Write-Host "--- Todo ---" -ForegroundColor Magenta
$todoBody = @{ user_id = $UserId; content = "写测试脚本"; priority = 2; due_date = "2025-12-31" }
$todo = Test-Api "添加待办" "POST" "/api/todo/add" -Body $todoBody
$todoId = $todo.id

Test-Api "待办列表" "GET" "/api/todo/list?user_id=$UserId"
Test-Api "已完成列表" "GET" "/api/todo/list?user_id=${UserId}&done=1"
Test-Api "标记完成" "POST" "/api/todo/done/$($todoId)?user_id=$UserId"
Test-Api "撤销完成" "POST" "/api/todo/undo/$($todoId)?user_id=$UserId"

$editBody = @{ content = "写测试脚本v2"; priority = 1 }
Test-Api "编辑待办" "PUT" "/api/todo/edit/$($todoId)?user_id=$UserId" -Body $editBody
#Test-Api "删除待办" "DELETE" "/api/todo/delete/$todoId?user_id=$UserId"
Write-Host ""

# --------------------------------------------------
# 5. Calendar
# --------------------------------------------------
Write-Host "--- Calendar ---" -ForegroundColor Magenta
$futureTime = (Get-Date).AddHours(2).ToString("yyyy-MM-dd HH:mm:ss")
$evtBody = @{ user_id = $UserId; title = "测试会议"; event_time = $futureTime; remind_before = 15; repeat = "none" }
$evt = Test-Api "添加日程" "POST" "/api/calendar/add" -Body $evtBody
$evtId = $evt.id

Test-Api "日程列表" "GET" "/api/calendar/list?user_id=${UserId}&days=60"
Test-Api "待触发提醒" "GET" "/api/calendar/pending_reminders?user_id=$UserId"
Test-Api "提醒日志" "GET" "/api/calendar/reminders_log?user_id=$UserId"
#Test-Api "删除日程" "DELETE" "/api/calendar/delete/$evtId?user_id=$UserId"
Write-Host ""

# --------------------------------------------------
# 6. Notify
# --------------------------------------------------
Write-Host "--- Notify ---" -ForegroundColor Magenta
$hookBody = @{ user_id = $UserId; name = "测试Webhook"; url = "https://httpbin.org/post"; method = "POST"; headers = "{}" }
Test-Api "保存Webhook" "POST" "/api/notify/webhook/save" -Body $hookBody
Test-Api "Webhook列表" "GET" "/api/notify/webhook/list?user_id=$UserId"

$notifyBody = @{ user_id = $UserId; channel = "webhook"; target = "测试Webhook"; title = "测试通知"; body = "这是一条测试消息" }
Test-Api "发送通知" "POST" "/api/notify/send" -Body $notifyBody
Test-Api "通知日志" "GET" "/api/notify/log?user_id=$UserId"
Write-Host ""

# --------------------------------------------------
# 7. Backup
# --------------------------------------------------
Write-Host "--- Backup ---" -ForegroundColor Magenta
Test-Api "创建备份" "POST" "/api/backup/create?name=test_backup_$UserId"
Test-Api "备份列表" "GET" "/api/backup/list"
Write-Host ""

# --------------------------------------------------
# 8. Data Exchange
# --------------------------------------------------
Write-Host "--- Data Exchange ---" -ForegroundColor Magenta
Test-Api "JSON导出" "GET" "/api/data/export/$UserId"
Test-Api "CSV导出-accounting" "GET" "/api/data/export/$UserId/csv/accounting"
Test-Api "CSV导出-todos" "GET" "/api/data/export/$UserId/csv/todos"

$importBody = @{
    user_id = $UserId
    data    = @{
        accounting = @(
            @{ amount = 50; category = "交通"; note = "导入测试" }
        )
    }
}
Test-Api "JSON导入" "POST" "/api/data/import" -Body $importBody
Write-Host ""

# --------------------------------------------------
# 9. Audit
# --------------------------------------------------
Write-Host "--- Audit ---" -ForegroundColor Magenta
Test-Api "审计日志" "GET" "/api/audit/log?user_id=${UserId}&limit=20"
Write-Host ""

# --------------------------------------------------
# 10. MCP Endpoint
# --------------------------------------------------
Write-Host "--- MCP ---" -ForegroundColor Magenta
Test-Api "MCP端点(健康)" "GET" "/mcp" -NoAuth -ExpectStatus 406
Write-Host ""

# --------------------------------------------------
# Summary
# --------------------------------------------------
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " 测试完成！" -ForegroundColor Cyan
Write-Host " 通过: $Passed  |  失败: $Failed  |  总计: $($Passed + $Failed)" -ForegroundColor Cyan
if ($Failed -eq 0) {
    Write-Host " 🎉 全部通过！" -ForegroundColor Green
} else {
    Write-Host " ⚠️  有 $Failed 个接口异常，请检查上方 ❌ 标记" -ForegroundColor Yellow
}
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "按 Enter 键退出"
