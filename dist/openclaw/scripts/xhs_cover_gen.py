#!/usr/bin/env python3
"""
xhs_cover_gen.py — Generate Xiaohongshu (RED) cover templates.

Creates 3:4 ratio cover images with text overlays for Xiaohongshu posts.
Supports multiple template styles: minimalist, bold, collage, gradient.

Usage:
    python3 scripts/xhs_cover_gen.py --title "AI工具推荐" --style minimalist
    python3 scripts/xhs_cover_gen.py --title "5个效率神器" --style bold --color "#FF6B6B"
    python3 scripts/xhs_cover_gen.py --title "干货分享" --style gradient --colors "#4ECDC4,#45B7D1"
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    from PIL import ImageFilter
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


WIDTH = 1080
HEIGHT = 1440  # 3:4 ratio

TEMPLATE_STYLES = {
    "minimalist": {
        "bg_color": "#FFFFFF",
        "text_color": "#1A1A2E",
        "accent_color": "#45B7D1",
        "font_size_title": 72,
        "font_size_subtitle": 36,
        "title_align": "center",
        "has_decoration": True,
        "decoration_type": "line",
    },
    "bold": {
        "bg_color": "#FF6B6B",
        "text_color": "#FFFFFF",
        "accent_color": "#FFEAA7",
        "font_size_title": 84,
        "font_size_subtitle": 40,
        "title_align": "left",
        "has_decoration": True,
        "decoration_type": "block",
    },
    "gradient": {
        "bg_color": "#4ECDC4",
        "text_color": "#FFFFFF",
        "accent_color": "#45B7D1",
        "font_size_title": 72,
        "font_size_subtitle": 36,
        "title_align": "center",
        "has_decoration": True,
        "decoration_type": "circle",
    },
    "dark": {
        "bg_color": "#1A1A2E",
        "text_color": "#FFFFFF",
        "accent_color": "#FF6B6B",
        "font_size_title": 72,
        "font_size_subtitle": 36,
        "title_align": "center",
        "has_decoration": True,
        "decoration_type": "dots",
    },
    "warm": {
        "bg_color": "#FFF5E6",
        "text_color": "#4A3728",
        "accent_color": "#FF9F43",
        "font_size_title": 68,
        "font_size_subtitle": 34,
        "title_align": "left",
        "has_decoration": True,
        "decoration_type": "wave",
    },
}


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_gradient_bg(width, height, color1, color2, direction="vertical"):
    img = Image.new("RGB", (width, height))
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)

    for y in range(height):
        for x in range(width):
            if direction == "vertical":
                ratio = y / height
            else:
                ratio = x / width
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            img.putpixel((x, y), (r, g, b))
    return img


def wrap_text(draw, text, font, max_width):
    words = list(text)
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)
    return lines


def draw_decoration(draw, style, width, height, accent_color):
    if style["decoration_type"] == "line":
        y_pos = height // 2 - 60
        draw.line(
            [(width // 4, y_pos), (3 * width // 4, y_pos)],
            fill=hex_to_rgb(accent_color),
            width=4,
        )
    elif style["decoration_type"] == "block":
        y_pos = height // 2 + 120
        draw.rectangle(
            [(60, y_pos), (140, y_pos + 8)],
            fill=hex_to_rgb(style["accent_color"]),
        )
    elif style["decoration_type"] == "circle":
        r = 80
        cx, cy = width // 2, height // 4
        for i in range(3):
            alpha = int(255 * (1 - i * 0.3))
            draw.ellipse(
                [(cx - r - i*30, cy - r - i*30), (cx + r + i*30, cy + r + i*30)],
                fill=(*hex_to_rgb(style["accent_color"]), alpha),
            )
    elif style["decoration_type"] == "dots":
        dot_color = hex_to_rgb(accent_color)
        for i in range(5):
            for j in range(5):
                x = width - 120 + j * 25
                y = height - 300 + i * 25
                draw.ellipse([(x, y), (x + 8, y + 8)], fill=dot_color)
    elif style["decoration_type"] == "wave":
        wave_color = hex_to_rgb(accent_color)
        for y in range(height - 200, height, 4):
            x_offset = int(30 * ((y % 40) / 40))
            draw.line(
                [(x_offset, y), (width - x_offset, y)],
                fill=(*wave_color, int(100 + (y - (height - 200)) * 0.5)),
                width=2,
            )


def get_font(size):
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_cover(title, subtitle="", style_name="minimalist", colors=None, output_path=None):
    style = TEMPLATE_STYLES.get(style_name, TEMPLATE_STYLES["minimalist"]).copy()

    if colors:
        if len(colors) == 1:
            style["bg_color"] = colors[0]
        elif len(colors) == 2:
            style["bg_color"] = colors[0]
            style["accent_color"] = colors[1]

    if style_name == "gradient" and colors and len(colors) >= 2:
        bg = create_gradient_bg(WIDTH, HEIGHT, colors[0], colors[1])
    else:
        bg = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(style["bg_color"]))

    draw = ImageDraw.Draw(bg)

    if style["has_decoration"]:
        draw_decoration(draw, style, WIDTH, HEIGHT, style["accent_color"])

    title_font = get_font(style["font_size_title"])
    subtitle_font = get_font(style["font_size_subtitle"])

    title_lines = wrap_text(draw, title, title_font, WIDTH - 160)
    line_height = style["font_size_title"] + 20
    total_title_height = len(title_lines) * line_height

    start_y = (HEIGHT - total_title_height) // 2
    if subtitle:
        start_y -= 40

    for i, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]

        if style["title_align"] == "center":
            x = (WIDTH - text_width) // 2
        else:
            x = 80

        y = start_y + i * line_height
        draw.text((x, y), line, font=title_font, fill=hex_to_rgb(style["text_color"]))

    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        sub_width = bbox[2] - bbox[0]
        sub_x = (WIDTH - sub_width) // 2 if style["title_align"] == "center" else 80
        sub_y = start_y + total_title_height + 30
        draw.text(
            (sub_x, sub_y),
            subtitle,
            font=subtitle_font,
            fill=hex_to_rgb(style["accent_color"]),
        )

    if output_path is None:
        output_path = f"xhs_cover_{style_name}.png"

    bg.save(output_path, "PNG")
    return output_path


def generate_batch(titles, style_name="minimalist", colors=None, output_dir=None):
    if output_dir is None:
        output_dir = Path.cwd() / "xhs_covers"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, item in enumerate(titles):
        title = item if isinstance(item, str) else item.get("title", f"Cover {i+1}")
        subtitle = "" if isinstance(item, str) else item.get("subtitle", "")
        output_path = output_dir / f"cover_{i+1:02d}.png"
        path = generate_cover(title, subtitle, style_name, colors, str(output_path))
        results.append(path)
        print(f"  Created: {path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Xiaohongshu cover template generator")
    parser.add_argument("--title", type=str, help="Cover title")
    parser.add_argument("--subtitle", type=str, default="", help="Cover subtitle")
    parser.add_argument("--style", type=str, default="minimalist",
                        choices=list(TEMPLATE_STYLES.keys()),
                        help="Template style")
    parser.add_argument("--color", type=str, default=None, help="Custom background color (hex)")
    parser.add_argument("--colors", type=str, default=None, help="Custom colors, comma-separated (hex)")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    parser.add_argument("--batch", type=str, default=None, help="JSON file with titles array for batch generation")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for batch mode")
    parser.add_argument("--list-styles", action="store_true", help="List available styles")
    args = parser.parse_args()

    if args.list_styles:
        print("Available cover styles:")
        for name, style in TEMPLATE_STYLES.items():
            print(f"  {name:12} - BG: {style['bg_color']}, Text: {style['text_color']}, Accent: {style['accent_color']}")
        return

    if args.batch:
        with open(args.batch, "r", encoding="utf-8") as f:
            titles = json.load(f)
        colors = None
        if args.colors:
            colors = [c.strip() for c in args.colors.split(",")]
        generate_batch(titles, args.style, colors, args.output_dir)
        print(f"Batch complete: {len(titles)} covers generated")
        return

    if not args.title:
        print("Error: --title is required (or use --batch for batch mode)")
        sys.exit(1)

    colors = None
    if args.colors:
        colors = [c.strip() for c in args.colors.split(",")]
    elif args.color:
        colors = [args.color]

    output_path = generate_cover(args.title, args.subtitle, args.style, colors, args.output)
    print(f"Cover generated: {output_path}")
    print(f"Style: {args.style}")
    print(f"Size: {WIDTH}x{HEIGHT} (3:4)")


if __name__ == "__main__":
    main()
