#!/usr/bin/env python3
"""
推送所有 tags 到 Gitea remote。

用法:
    python scripts/push-gitea.py
"""

import subprocess
import sys


def get_latest_tag() -> str | None:
    result = subprocess.run(
        ["git", "tag", "--sort=-v:refname"],
        capture_output=True, text=True, check=True,
    )
    tags = [t.strip() for t in result.stdout.strip().splitlines() if t.strip()]
    return tags[0] if tags else None


def main() -> None:
    tag = get_latest_tag()
    if tag:
        print(f"📌 最新 tag: {tag}")
    else:
        print("📌 暂无 tag")

    print(f"📤 推送 tags 到 gitea ...")
    result = subprocess.run(["git", "push", "gitea", "--tags"])
    if result.returncode != 0:
        print("❌ 推送失败")
        sys.exit(result.returncode)
    print("✅ 推送成功")


if __name__ == "__main__":
    main()
