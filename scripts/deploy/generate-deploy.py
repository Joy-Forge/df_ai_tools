#!/usr/bin/env python3
"""
生成 dist/deploy/ 生产部署包

用法:
    python scripts/deploy/generate-deploy.py                    # 从 git remote 自动推断
    python scripts/deploy/generate-deploy.py --owner myuser     # 显式指定 owner
    python scripts/deploy/generate-deploy.py --tag v1.2.3       # 指定镜像标签（CI Release 用）

自动从 git remote 提取的信息:
    - OWNER: GitHub 用户名或组织名
    - REPO_NAME: 仓库名称（如 agent-tools-kit）
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "scripts" / "deploy" / "templates"
OUTPUT_DIR = REPO_ROOT / "dist" / "deploy"

DEFAULT_VALUES = {
    "REGISTRY": "ghcr.io",
    "REPO_NAME": "agent-tools-kit",
    "IMAGE_TAG": "latest",
    "CONTAINER_NAME": "agent_tools_kit",
    "HOST_PORT": "8000",
    "DB_PATH": "/app/data/toolkit.db",
}


def get_git_remote_owner() -> str | None:
    """从 git remote 提取 owner（用户名/组织名），支持任意 remote 名称"""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True, text=True, check=True, cwd=REPO_ROOT,
        )
        for line in result.stdout.strip().splitlines():
            url = line.split("\t")[1].split()[0] if "\t" in line else ""
            # git@host:owner/repo.git  → owner
            # https://host/owner/repo.git  → owner
            # http://host:port/owner/repo.git  → owner
            match = re.search(r"[:/]([^/]+)/(?:[^/]+?)(?:\.git)?$", url)
            if match:
                return match.group(1).lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def get_git_repo_name() -> str | None:
    """从 git remote 提取仓库名，支持任意 remote 名称"""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True, text=True, check=True, cwd=REPO_ROOT,
        )
        for line in result.stdout.strip().splitlines():
            url = line.split("\t")[1].split()[0] if "\t" in line else ""
            match = re.search(r"/([^/]+?)(?:\.git)?$", url)
            if match:
                return match.group(1).lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 dist/deploy/ 部署包")
    parser.add_argument("--owner", help="GitHub 用户名/组织名（覆盖 git remote 自动检测）")
    parser.add_argument("--repo", help="镜像仓库名（覆盖 git remote 自动检测，默认 agent-tools-kit）")
    parser.add_argument("--tag", help="镜像标签（默认 latest，CI Release 时传入版本号如 v1.2.3）")
    parser.add_argument("--port", help="宿主机映射端口（默认 8000）")
    parser.add_argument("--output", help="输出目录（默认 dist/deploy）")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # --- 确定 owner ---
    owner = args.owner or get_git_remote_owner()
    if not owner:
        print("错误: 无法从 git remote 推断 owner，请用 --owner 显式指定")
        sys.exit(1)

    # --- 确定 repo name ---
    repo_name = args.repo or get_git_repo_name() or DEFAULT_VALUES["REPO_NAME"]

    # --- 确定输出目录 ---
    output_dir = Path(args.output) if args.output else OUTPUT_DIR

    # --- 构建替换映射 ---
    replacements = {**DEFAULT_VALUES}
    replacements["OWNER"] = owner
    replacements["REPO_NAME"] = repo_name
    if args.tag:
        replacements["IMAGE_TAG"] = args.tag
    if args.port:
        replacements["HOST_PORT"] = args.port

    # --- 清理并重建输出目录 ---
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # --- 处理每个模板文件 ---
    if not TEMPLATE_DIR.exists():
        print(f"错误: 模板目录不存在: {TEMPLATE_DIR}")
        sys.exit(1)

    for template_path in sorted(TEMPLATE_DIR.iterdir()):
        if not template_path.is_file():
            continue
        content = template_path.read_text(encoding="utf-8")
        for key, value in replacements.items():
            content = content.replace("{{" + key + "}}", value)
        out_path = output_dir / template_path.name
        out_path.write_text(content, encoding="utf-8")
        # 保持 run.sh 的可执行权限
        if template_path.suffix == ".sh":
            out_path.chmod(0o755)

    print("=== 部署包已生成 ===")
    print(f"  Output:     {output_dir}")
    print(f"  Owner:      {owner}")
    print(f"  Repo:       {repo_name}")
    print(f"  Image:      {replacements['REGISTRY']}/{owner}/{repo_name}:{replacements['IMAGE_TAG']}")
    print(f"  Container:  {replacements['CONTAINER_NAME']}")
    print(f"  Port:       {replacements['HOST_PORT']}:8000")


if __name__ == "__main__":
    main()
