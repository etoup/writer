#!/usr/bin/env python3
"""Export all 12 platform articles and generate a single .docx usage guide."""

import sys
sys.path.insert(0, "/Users/yuesu/Documents/Skills/wewrite/toolkit")

from pathlib import Path
from exporter import (
    export_platform,
    generate_usage_docx,
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

# Generate a single .docx usage guide (includes file list + image list + tips)
doc_path = generate_usage_docx(OUTPUT_DIR, platform_files)
print(f"Generated {Path(doc_path).name}")

print("\nDone! All files exported to:", OUTPUT_DIR)
