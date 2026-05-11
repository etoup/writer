#!/usr/bin/env python3
"""Test image generation and verify image gallery."""

import sys
sys.path.insert(0, "/Users/yuesu/Documents/Skills/wewrite/toolkit")

from pathlib import Path
from image_gen import generate_image

OUTPUT_DIR = "/Users/yuesu/Documents/Skills/wewrite/output/2026-05-10-ai-writing"
IMAGES_DIR = Path(OUTPUT_DIR) / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Generate a cover image for the AI writing topic
cover_prompt = (
    "A conceptual illustration showing a human hand holding a pen next to "
    "a glowing AI robot arm holding a digital stylus, both writing on paper. "
    "Warm lighting, professional editorial atmosphere, no text, no letters, "
    "no words, clean space for text overlay on the right side."
)

print("Generating cover image...")
try:
    cover_path = generate_image(
        prompt=cover_prompt,
        output_path=str(IMAGES_DIR / "cover_01.png"),
        size="cover",
    )
    print(f"Cover image saved: {cover_path}")
except Exception as e:
    print(f"Cover image failed: {e}")
    sys.exit(1)

# Generate an article illustration
article_prompt = (
    "A split composition showing traditional handwritten letters on one side "
    "and glowing digital text flowing on a screen on the other side, "
    "symbolizing the contrast between human and AI writing. "
    "Modern editorial style, no text, no letters, no words."
)

print("Generating article image...")
try:
    article_path = generate_image(
        prompt=article_prompt,
        output_path=str(IMAGES_DIR / "article_01_comparison.png"),
        size="article",
    )
    print(f"Article image saved: {article_path}")
except Exception as e:
    print(f"Article image failed: {e}")
    sys.exit(1)

print("\nAll images generated successfully!")
