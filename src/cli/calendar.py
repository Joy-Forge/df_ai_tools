"""Calendar CLI commands."""

from __future__ import annotations

import click

from .utils import build_client, fmt_iso, request


@click.group()
@click.pass_context
def calendar(ctx: click.Context) -> None:
    """管理日程事件"""


@calendar.command("list")
@click.option("--days", default=30, show_default=True, help="未来多少天内的日程")
@click.option("--limit", default=50, show_default=True, help="返回条数上限")
@click.option("--offset", default=0, show_default=True, help="分页偏移")
@click.pass_context
def list_calendar(ctx: click.Context, days: int, limit: int, offset: int) -> None:
    """查询日程列表"""
    client = ctx.obj["client"]
    data = request(client, "GET", "/api/calendar/list", params={
        "user_id": ctx.obj["user_id"], "days": days, "limit": limit, "offset": offset,
    })

    if not data:
        click.echo("暂无日程事件。")
        return

    for item in data:
        repeat = f" [重复: {item['repeat']}]" if item.get("repeat") else ""
        reminded = " [已提醒]" if item["reminded"] else ""
        click.echo(f"  #{item['id']}  {fmt_iso(item['event_time'])}  {item['title']}{repeat}{reminded}")


@calendar.command("add")
@click.option("--title", required=True, help="事件标题")
@click.option("--event-time", required=True, help="ISO 格式时间，如 2026-06-15T09:00:00")
@click.option("--remind-before", type=click.INT, default=10, show_default=True, help="提前多少分钟提醒")
@click.option("--repeat", type=click.Choice(["daily", "weekly", "monthly"]), help="重复模式")
@click.pass_context
def add_calendar(ctx: click.Context, title: str, event_time: str, remind_before: int, repeat: str | None) -> None:
    """添加日程事件"""
    client = ctx.obj["client"]
    body = {
        "user_id": ctx.obj["user_id"],
        "title": title,
        "event_time": event_time,
        "remind_before": remind_before,
        "repeat": repeat or "",
    }
    data = request(client, "POST", "/api/calendar/add", json_body=body)
    click.echo(data["msg"])


@calendar.command("delete")
@click.argument("event_id", type=click.INT)
@click.pass_context
def delete_calendar(ctx: click.Context, event_id: int) -> None:
    """删除日程事件"""
    client = ctx.obj["client"]
    data = request(client, "DELETE", f"/api/calendar/delete/{event_id}", params={"user_id": ctx.obj["user_id"]})
    click.echo(data["msg"])


@calendar.command("pending-reminders")
@click.pass_context
def pending_reminders(ctx: click.Context) -> None:
    """查询待提醒事件"""
    client = ctx.obj["client"]
    data = request(client, "GET", "/api/calendar/pending_reminders", params={"user_id": ctx.obj["user_id"]})

    if not data:
        click.echo("暂无待提醒事件。")
        return

    for item in data:
        click.echo(f"  #{item['id']}  {fmt_iso(item['event_time'])}  {item['title']}")


@calendar.command("reminders-log")
@click.option("--limit", default=50, show_default=True, help="返回条数上限")
@click.pass_context
def reminders_log(ctx: click.Context, limit: int) -> None:
    """查询提醒发送记录"""
    client = ctx.obj["client"]
    data = request(client, "GET", "/api/calendar/reminders_log", params={
        "user_id": ctx.obj["user_id"], "limit": limit,
    })

    if not data:
        click.echo("暂无提醒记录。")
        return

    for item in data:
        click.echo(f"  {fmt_iso(item['sent_at'])}  {item['title']}")
