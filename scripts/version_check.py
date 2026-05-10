#!/usr/bin/env python3
"""
version_check.py — Check for Writer version updates and display changelog.

Compares local VERSION with remote git version, shows what's new.
Supports manual check and automatic check (called during Step 1.2).

Usage:
    python3 scripts/version_check.py
    python3 scripts/version_check.py --json
    python3 scripts/version_check.py --skip-check
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def get_local_version(skill_dir):
    version_file = Path(skill_dir) / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "unknown"


def get_remote_version(skill_dir):
    try:
        result = subprocess.run(
            ["git", "show", "origin/main:VERSION"],
            cwd=skill_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_changelog(skill_dir):
    changelog_path = Path(skill_dir) / "CHANGELOG.md"
    if changelog_path.exists():
        return changelog_path.read_text(encoding="utf-8")
    return None


def get_recent_commits(skill_dir, count=10):
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-{count}"],
            cwd=skill_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")
    except Exception:
        pass
    return []


def parse_version(ver_str):
    """Parse version string to tuple of ints for comparison."""
    try:
        return tuple(int(x) for x in ver_str.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_update(skill_dir):
    local_ver = get_local_version(skill_dir)
    remote_ver = get_remote_version(skill_dir)

    if remote_ver is None:
        return {
            "status": "unknown",
            "local_version": local_ver,
            "remote_version": None,
            "message": "无法获取远程版本（可能没有 .git 目录或网络不可用）",
        }

    local_parsed = parse_version(local_ver)
    remote_parsed = parse_version(remote_ver)

    if local_parsed >= remote_parsed:
        return {
            "status": "up_to_date",
            "local_version": local_ver,
            "remote_version": remote_ver,
            "message": f"当前已是最新版本 ({local_ver})" + 
                      ("（本地版本领先远程）" if local_parsed > remote_parsed else ""),
        }

    commits = get_recent_commits(skill_dir)
    changelog = get_changelog(skill_dir)

    return {
        "status": "update_available",
        "local_version": local_ver,
        "remote_version": remote_ver,
        "message": f"有新版本可用：{local_ver} → {remote_ver}",
        "recent_commits": commits,
        "has_changelog": changelog is not None,
    }


def main():
    parser = argparse.ArgumentParser(description="Writer version update checker")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--skip-check", action="store_true", help="Skip git fetch, only show local version")
    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent

    if args.skip_check:
        local_ver = get_local_version(skill_dir)
        if args.json:
            print(json.dumps({"local_version": local_ver, "status": "skipped"}, indent=2))
        else:
            print(f"Writer 本地版本: {local_ver}")
        return

    result = check_update(skill_dir)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"Writer 版本检查")
    print(f"本地版本: {result['local_version']}")

    if result["status"] == "unknown":
        print(f"远程版本: 无法获取")
        print(result["message"])
    elif result["status"] == "up_to_date":
        print(f"远程版本: {result['remote_version']}")
        print(f"状态: 已是最新")
    else:
        print(f"远程版本: {result['remote_version']}")
        print(f"状态: 有更新可用")
        print(f"\n最近提交:")
        for commit in result.get("recent_commits", [])[:5]:
            print(f"  {commit}")

        if result.get("has_changelog"):
            print(f"\n查看完整更新日志: CHANGELOG.md")

        print(f"\n执行更新: git pull origin main")


if __name__ == "__main__":
    main()
