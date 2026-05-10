#!/usr/bin/env python3
"""Export all 12 platform articles and generate HTML list files."""

import sys
sys.path.insert(0, "/Users/yuesu/Documents/Skills/wewrite/toolkit")

from pathlib import Path
from exporter import (
    export_platform,
    generate_usage_guide,
    generate_image_gallery_html,
    generate_file_preview_html,
    PLATFORM_DISPLAY_NAMES,
)

OUTPUT_DIR = "/Users/yuesu/Documents/Skills/wewrite/output/2026-05-10-ai-writing"

# Read each platform's md and export
platforms = [
    "wechat", "xiaohongshu", "zhihu", "baijiahao",
    "weibo", "sohu", "toutiao", "qiehao",
    "jianshu", "douban", "dayu", "kr36",
]

platform_files = {}

for platform in platforms:
    md_file = Path(OUTPUT_DIR) / f"{platform}.md"
    if not md_file.exists():
        print(f"SKIP: {md_file} not found")
        continue

    md_content = md_file.read_text(encoding="utf-8")
    result = export_platform(
        md_content=md_content,
        platform=platform,
        output_dir=OUTPUT_DIR,
    )
    platform_files[platform] = result
    print(f"Exported {platform}: {list(result.keys())}")

# Generate HTML list files
generate_usage_guide(OUTPUT_DIR, platform_files)
print("Generated README_文件说明.html")

generate_image_gallery_html(OUTPUT_DIR)
print("Generated 图片清单.html")

generate_file_preview_html(OUTPUT_DIR, platform_files)
print("Generated 文件清单_可点击预览.html")

print("\nDone! All files exported to:", OUTPUT_DIR)
