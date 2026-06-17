"""Todo CLI commands."""

from __future__ import annotations

from typing import Any

import click

from .utils import build_client, fmt_iso, request

PRIORITY_LABELS = {1: "[高]", 2: "[中]", 3: "[低]"}


@click.group()
@click.pass_context
def todo(ctx: click.Context) -> None:
    """管理待办事项"""


@todo.command("list")
@click.option("--done", type=click.INT, help="筛选: 0=未完成, 1=已完成 (不传=全部)")
@click.option("--limit", default=50, show_default=True, help="返回条数上限")
@click.option("--offset", default=0, show_default=True, help="分页偏移")
@click.pass_context
def list_todos(ctx: click.Context, done: int | None, limit: int, offset: int) -> None:
    """查询待办列表"""
    client = ctx.obj["client"]
    params: dict[str, Any] = {"user_id": ctx.obj["user_id"], "limit": limit, "offset": offset}
    if done is not None:
        params["done"] = done
    data = request(client, "GET", "/api/todo/list", params=params)

    if not data:
        click.echo("暂无待办事项。")
        return

    for item in data:
        pri = PRIORITY_LABELS.get(item.get("priority", 1), "?")
        status = "[V]" if item["done"] else "[ ]"
        due = f" 截止: {item['due_date']}" if item.get("due_date") else ""
        click.echo(f"  #{item['id']} {status} {pri} {item['content']}{due}")
        click.echo(f"      创建: {fmt_iso(item['time'])}")


@todo.command("add")
@click.argument("content")
@click.option("--priority", type=click.IntRange(1, 3), default=1, show_default=True, help="优先级 1(高)~3(低)")
@click.option("--due", default="", help="截止日期 (自由文本)")
@click.pass_context
def add_todo(ctx: click.Context, content: str, priority: int, due: str) -> None:
    """添加待办事项"""
    client = ctx.obj["client"]
    body = {"user_id": ctx.obj["user_id"], "content": content, "priority": priority, "due_date": due}
    data = request(client, "POST", "/api/todo/add", json_body=body)
    click.echo(data["msg"])


@todo.command("done")
@click.argument("todo_id", type=click.INT)
@click.pass_context
def done_todo(ctx: click.Context, todo_id: int) -> None:
    """标记待办为已完成"""
    client = ctx.obj["client"]
    data = request(client, "POST", f"/api/todo/done/{todo_id}", params={"user_id": ctx.obj["user_id"]})
    click.echo(data["msg"])


@todo.command("undo")
@click.argument("todo_id", type=click.INT)
@click.pass_context
def undo_todo(ctx: click.Context, todo_id: int) -> None:
    """恢复待办为未完成"""
    client = ctx.obj["client"]
    data = request(client, "POST", f"/api/todo/undo/{todo_id}", params={"user_id": ctx.obj["user_id"]})
    click.echo(data["msg"])


@todo.command("delete")
@click.argument("todo_id", type=click.INT)
@click.pass_context
def delete_todo(ctx: click.Context, todo_id: int) -> None:
    """删除待办事项"""
    client = ctx.obj["client"]
    data = request(client, "DELETE", f"/api/todo/delete/{todo_id}", params={"user_id": ctx.obj["user_id"]})
    click.echo(data["msg"])


@todo.command("edit")
@click.argument("todo_id", type=click.INT)
@click.option("--content", help="新内容")
@click.option("--priority", type=click.IntRange(1, 3), help="新优先级 1(高)~3(低)")
@click.option("--due", help="新截止日期")
@click.pass_context
def edit_todo(ctx: click.Context, todo_id: int, content: str | None, priority: int | None, due: str | None) -> None:
    """编辑待办事项 (至少提供一个修改字段)"""
    client = ctx.obj["client"]
    body: dict[str, Any] = {}
    if content is not None:
        body["content"] = content
    if priority is not None:
        body["priority"] = priority
    if due is not None:
        body["due_date"] = due
    if not body:
        click.echo("请至少提供一个修改字段: --content / --priority / --due", err=True)
        raise SystemExit(1)
    data = request(client, "PUT", f"/api/todo/edit/{todo_id}", params={"user_id": ctx.obj["user_id"]}, json_body=body)
    click.echo(data["msg"])
