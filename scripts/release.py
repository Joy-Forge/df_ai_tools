#!/usr/bin/env python3
"""
一键发布脚本 — 输入版本号，自动打 tag 并推送到 GitHub (origin remote)。

如果你有多个 remote（如 gitea），推送完 origin 后请手动运行：
    git push gitea <tag>

用法:
    python scripts/release.py
"""

import subprocess
import sys
import re


def get_current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def get_latest_tag() -> str | None:
    result = subprocess.run(
        ["git", "tag", "--sort=-v:refname"],
        capture_output=True, text=True, check=True,
    )
    tags = [t.strip() for t in result.stdout.strip().splitlines() if t.strip()]
    return tags[0] if tags else None


def tag_exists(tag: str) -> bool:
    result = subprocess.run(
        ["git", "tag", "-l", tag],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip() == tag


def main() -> None:
    # 1. 检查是否在 main 分支
    branch = get_current_branch()
    if branch != "main":
        print(f"⚠️  当前不在 main 分支 (当前: {branch})，建议切换到 main 再发布。")
        confirm = input("  仍然继续？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消。")
            sys.exit(1)

    # 2. 检查是否有未提交的修改
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    )
    if result.stdout.strip():
        print("⚠️  有未提交的修改，请先 commit 或 stash。")
        sys.exit(1)

    # 3. 显示最近的 tag
    latest = get_latest_tag()
    if latest:
        print(f"📌 上一个 tag: {latest}")
    else:
        print("📌 暂无 tag")

    # 4. 输入版本号
    tag = input("\n输入版本号 (例如 1.0.0，不需要 v 前缀): ").strip()
    if not tag:
        print("版本号不能为空。")
        sys.exit(1)

    # 补上 v 前缀
    if not tag.startswith("v"):
        tag = f"v{tag}"

    # 校验格式
    if not re.match(r"^v\d+\.\d+\.\d+", tag):
        print(f"⚠️  版本号格式不标准 (建议 vMAJOR.MINOR.PATCH，如 v1.0.0)")
        confirm = input(f"  仍然使用「{tag}」？(y/N): ").strip().lower()
        if confirm != "y":
            print("已取消。")
            sys.exit(1)

    # 5. 检查 tag 是否已存在
    if tag_exists(tag):
        print(f"❌  tag「{tag}」已存在，请使用更高的版本号。")
        sys.exit(1)

    # 6. 确认
    print(f"\n{'='*40}")
    print(f"  版本:    {tag}")
    print(f"  分支:    {branch}")
    print(f"{'='*40}")
    confirm = input("\n确认发布？(y/N): ").strip().lower()
    if confirm != "y":
        print("已取消。")
        sys.exit(1)

    # 7. 打标签并推送
    print(f"\n🚀 创建 tag {tag} ...")
    subprocess.run(["git", "tag", tag], check=True)

    print(f"📤 推送 tag 到 origin (GitHub) ...")
    subprocess.run(["git", "push", "origin", tag], check=True)

    print(f"\n✅ 发布成功！GitHub Actions 正在运行：")
    print(f"   https://github.com/Joy-Forge/df_ai_tools/actions")
    print(f"   将自动构建 Docker 镜像并创建 Release。")


if __name__ == "__main__":
    main()
