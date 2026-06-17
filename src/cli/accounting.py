"""Accounting CLI commands."""

from __future__ import annotations

from typing import Any

import click

from .utils import build_client, fmt_iso, request


@click.group()
@click.pass_context
def accounting(ctx: click.Context) -> None:
    """管理记账记录"""


@accounting.command("list")
@click.option("--limit", default=50, show_default=True, help="返回条数上限")
@click.option("--offset", default=0, show_default=True, help="分页偏移")
@click.pass_context
def list_accounting(ctx: click.Context, limit: int, offset: int) -> None:
    """查询记账记录"""
    client = ctx.obj["client"]
    data = request(client, "GET", "/api/accounting/list", params={
        "user_id": ctx.obj["user_id"], "limit": limit, "offset": offset,
    })

    if not data:
        click.echo("暂无记账记录。")
        return

    total = 0.0
    for item in data:
        total += item["amount"]
        click.echo(f"  #{item['id']}  {item['category']:8s}  {item['amount']:>8.2f}  {item.get('note', ''):20s}  {fmt_iso(item['time'])}")
    click.echo(f"  --- 合计: {total:.2f}")


@accounting.command("add")
@click.argument("amount", type=click.FLOAT)
@click.option("--category", required=True, help="分类，如 餐饮、交通")
@click.option("--note", default="", help="备注")
@click.pass_context
def add_accounting(ctx: click.Context, amount: float, category: str, note: str) -> None:
    """添加记账记录"""
    client = ctx.obj["client"]
    body = {"user_id": ctx.obj["user_id"], "amount": amount, "category": category, "note": note}
    data = request(client, "POST", "/api/accounting/add", json_body=body)
    click.echo(data["msg"])


@accounting.command("summary")
@click.pass_context
def summary_accounting(ctx: click.Context) -> None:
    """获取记账汇总统计"""
    client = ctx.obj["client"]
    data = request(client, "GET", "/api/accounting/summary", params={"user_id": ctx.obj["user_id"]})

    click.echo(f"  总支出: {data['total']:.2f}")
    click.echo("  按分类:")
    for cat, amount in data.get("by_category", {}).items():
        click.echo(f"    {cat:10s}  {amount:.2f}")


@accounting.command("delete")
@click.argument("record_id", type=click.INT)
@click.pass_context
def delete_accounting(ctx: click.Context, record_id: int) -> None:
    """删除记账记录"""
    client = ctx.obj["client"]
    data = request(client, "DELETE", f"/api/accounting/delete/{record_id}", params={"user_id": ctx.obj["user_id"]})
    click.echo(data["msg"])


@accounting.command("update")
@click.argument("record_id", type=click.INT)
@click.option("--amount", type=click.FLOAT, help="新金额")
@click.option("--category", help="新分类")
@click.option("--note", help="新备注")
@click.pass_context
def update_accounting(ctx: click.Context, record_id: int, amount: float | None, category: str | None, note: str | None) -> None:
    """更新记账记录 (至少提供一个修改字段)"""
    client = ctx.obj["client"]
    body: dict[str, Any] = {}
    if amount is not None:
        body["amount"] = amount
    if category is not None:
        body["category"] = category
    if note is not None:
        body["note"] = note
    if not body:
        click.echo("请至少提供一个修改字段: --amount / --category / --note", err=True)
        raise SystemExit(1)
    data = request(client, "PUT", f"/api/accounting/update/{record_id}", params={"user_id": ctx.obj["user_id"]}, json_body=body)
    click.echo(data["msg"])
