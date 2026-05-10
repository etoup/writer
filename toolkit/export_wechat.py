#!/usr/bin/env python3
"""Export a single WeChat article and generate HTML list files."""

import sys
sys.path.insert(0, "/Users/yuesu/Documents/Skills/wewrite/toolkit")

from pathlib import Path
from exporter import (
    export_platform,
    generate_usage_guide,
    generate_image_gallery_html,
    generate_file_preview_html,
)

OUTPUT_DIR = "/Users/yuesu/Documents/Skills/wewrite/output/2026-05-10-young-solitude"
PLATFORM = "wechat"

# Read the wechat md and export
md_file = Path(OUTPUT_DIR) / f"{PLATFORM}.md"
if not md_file.exists():
    print(f"ERROR: {md_file} not found")
    sys.exit(1)

md_content = md_file.read_text(encoding="utf-8")
result = export_platform(
    md_content=md_content,
    platform=PLATFORM,
    output_dir=OUTPUT_DIR,
)
print(f"Exported {PLATFORM}: {list(result.keys())}")

# Generate HTML list files
platform_files = {PLATFORM: result}
generate_usage_guide(OUTPUT_DIR, platform_files)
print("Generated README_文件说明.html")

generate_image_gallery_html(OUTPUT_DIR)
print("Generated 图片清单.html")

generate_file_preview_html(OUTPUT_DIR, platform_files)
print("Generated 文件清单_可点击预览.html")

print("\nDone! All files exported to:", OUTPUT_DIR)
