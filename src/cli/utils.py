"""Shared HTTP client for aitools CLI."""

from __future__ import annotations

import json
import sys
from typing import Any

import click
import httpx


def build_client(server: str, api_key: str | None) -> httpx.Client:
    """Create an httpx.Client pointed at the aitools server."""
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    # Strip trailing slash from server URL
    base_url = server.rstrip("/")
    return httpx.Client(base_url=base_url, headers=headers, timeout=30.0)


def request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make an HTTP request and return parsed JSON.

    On failure, prints the error and exits the process.
    """
    try:
        resp = client.request(method, path, params=params, json=json_body)
    except httpx.ConnectError as exc:
        _fail(f"无法连接到服务器: {exc}\n请确认 aitools 服务正在运行。")

    if resp.is_error:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        _fail(f"请求失败 [{resp.status_code}]: {detail}")

    # Handle non-JSON or empty 2xx responses gracefully
    if not resp.content:
        return {}
    try:
        return resp.json()
    except json.JSONDecodeError:
        return {"raw": resp.text}


def _fail(msg: str) -> None:
    """Print an error message and exit."""
    click.echo(click.style("错误: ", fg="red", bold=True) + msg, err=True)
    sys.exit(1)


def fmt_iso(iso_str: str) -> str:
    """Format an ISO datetime string for human display."""
    return iso_str.replace("T", " ")
