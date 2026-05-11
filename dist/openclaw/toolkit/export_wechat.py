#!/usr/bin/env python3
"""Export a single WeChat article and generate a single .docx usage guide."""

import sys
sys.path.insert(0, "/Users/yuesu/Documents/Skills/wewrite/toolkit")

from pathlib import Path
from exporter import (
    export_platform,
    generate_usage_docx,
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

# Generate a single .docx usage guide
platform_files = {PLATFORM: result}
doc_path = generate_usage_docx(OUTPUT_DIR, platform_files)
print(f"Generated {Path(doc_path).name}")

print("\nDone! All files exported to:", OUTPUT_DIR)
