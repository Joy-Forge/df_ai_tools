"""Notify CLI commands."""

from __future__ import annotations

import json

import click

from .utils import build_client, fmt_iso, request


@click.group()
@click.pass_context
def notify(ctx: click.Context) -> None:
    """管理通知"""


@notify.command("webhook-save")
@click.option("--name", required=True, help="Webhook 名称")
@click.option("--url", required=True, help="Webhook URL")
@click.option("--method", default="POST", show_default=True, type=click.Choice(["POST", "GET"]), help="HTTP 方法")
@click.option("--headers", default="{}", help="自定义请求头 (JSON 字符串，如 '{\"Authorization\": \"Bearer xxx\"}')")
@click.pass_context
def webhook_save(ctx: click.Context, name: str, url: str, method: str, headers: str) -> None:
    """保存 Webhook 配置"""
    # Validate JSON
    try:
        json.loads(headers)
    except json.JSONDecodeError as exc:
        click.echo(f"错误: --headers 参数不是合法的 JSON: {exc}", err=True)
        raise SystemExit(1)
    client = ctx.obj["client"]
    body = {
        "user_id": ctx.obj["user_id"],
        "name": name,
        "url": url,
        "method": method,
        "headers": headers,
    }
    data = request(client, "POST", "/api/notify/webhook/save", json_body=body)
    click.echo(data["msg"])


@notify.command("webhook-list")
@click.pass_context
def webhook_list(ctx: click.Context) -> None:
    """查询 Webhook 列表"""
    client = ctx.obj["client"]
    data = request(client, "GET", "/api/notify/webhook/list", params={"user_id": ctx.obj["user_id"]})

    if not data:
        click.echo("暂无 Webhook 配置。")
        return

    for item in data:
        click.echo(f"  #{item['id']}  {item['name']:20s}  {item['method']:6s}  {item['url']}")


@notify.command("send")
@click.option("--channel", required=True, default="webhook", show_default=True, help="通知通道 (目前仅支持 webhook)")
@click.option("--target", required=True, help="目标: webhook 的 name")
@click.option("--title", required=True, help="通知标题")
@click.option("--body", required=True, help="通知正文")
@click.pass_context
def send_notify(ctx: click.Context, channel: str, target: str, title: str, body: str) -> None:
    """发送通知"""
    client = ctx.obj["client"]
    body_data = {
        "user_id": ctx.obj["user_id"],
        "channel": channel,
        "target": target,
        "title": title,
        "body": body,
    }
    data = request(client, "POST", "/api/notify/send", json_body=body_data)
    click.echo(f"状态: {data['status']}")


@notify.command("log")
@click.option("--limit", default=50, show_default=True, help="返回条数上限")
@click.option("--offset", default=0, show_default=True, help="分页偏移")
@click.pass_context
def notify_log(ctx: click.Context, limit: int, offset: int) -> None:
    """查询通知发送日志"""
    client = ctx.obj["client"]
    data = request(client, "GET", "/api/notify/log", params={
        "user_id": ctx.obj["user_id"], "limit": limit, "offset": offset,
    })

    if not data:
        click.echo("暂无通知日志。")
        return

    for item in data:
        click.echo(f"  {fmt_iso(item['time'])}  [{item['channel']}] → {item['target']:20s}  {item['title']:20s}  status={item['status']}")
