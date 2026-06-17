"""Agent Tools Kit — CLI

Usage:
    aitools [--server URL] [--api-key KEY] [--user USER] <command> <subcommand> [args]

Examples:
    aitools todo list
    aitools todo add "买牛奶" --priority 2
    aitools accounting add 25.5 --category 餐饮 --note "午餐"
    aitools accounting summary
    aitools calendar list --days 7
    aitools calendar add --title "会议" --event-time "2026-06-20T14:00:00"
    aitools notify send --channel webhook --target my_hook --title "提醒" --body "到时间了"
    aitools health
"""

from __future__ import annotations

import os

import click

from . import accounting, calendar, notify, todo
from .utils import build_client, request


@click.group()
@click.option("--server", default=os.getenv("AITOOLS_SERVER", "http://127.0.0.1:8000"), show_default=True,
              help="aitools 服务地址")
@click.option("--api-key", default=os.getenv("AITOOLS_API_KEY", ""), help="API Key (也可通过 AITOOLS_API_KEY 环境变量设置)")
@click.option("--user", default=os.getenv("AITOOLS_USER", "default"), show_default=True,
              help="用户标识 (也可通过 AITOOLS_USER 环境变量设置)")
@click.pass_context
def cli(ctx: click.Context, server: str, api_key: str, user: str) -> None:
    """Agent Tools Kit — 记账 / 待办 / 日历 / 通知

    通过命令行管理你的个人数据，需要先启动 aitools 服务。
    """
    ctx.ensure_object(dict)
    ctx.obj["client"] = build_client(server, api_key or None)
    ctx.obj["user_id"] = user


@cli.command()
@click.pass_context
def health(ctx: click.Context) -> None:
    """检查 aitools 服务健康状态"""
    client = ctx.obj["client"]
    data = request(client, "GET", "/api/health")
    click.echo(f"状态: {data['status']}")
    click.echo(f"MCP 工具数: {data['tools']}")


cli.add_command(todo.todo)
cli.add_command(accounting.accounting)
cli.add_command(calendar.calendar)
cli.add_command(notify.notify)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
