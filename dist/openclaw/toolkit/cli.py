#!/usr/bin/env python3
"""
CLI entry point for Writer.

Usage:
    python cli.py preview article.md --theme professional-clean
    python cli.py export article.md --platform wechat --output ./output/
    python cli.py export article.md --platform all --output ./output/
    python cli.py themes
"""

import argparse
import re
import sys
import webbrowser
from pathlib import Path

import yaml

from converter import WeChatConverter, preview_html
from theme import load_theme, list_themes
from exporter import export_platform, export_all_platforms, generate_usage_guide, generate_image_gallery_html, generate_file_preview_html, PLATFORM_DISPLAY_NAMES
from platform_writer import write_for_platforms, PLATFORM_SPECS
from platform_images import generate_platform_images, PLATFORM_IMAGE_CONFIGS

# Config file search order
CONFIG_PATHS = [
    Path.cwd() / "config.yaml",
    Path(__file__).parent.parent / "config.yaml",  # skill root
    Path(__file__).parent / "config.yaml",          # toolkit dir
    Path.home() / ".config" / "writer" / "config.yaml",
]


def load_config() -> dict:
    """Load config from first found config.yaml."""
    for p in CONFIG_PATHS:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


def cmd_preview(args):
    """Generate HTML preview and open in browser."""
    theme = load_theme(args.theme)
    converter = WeChatConverter(theme=theme)
    result = converter.convert_file(args.input)

    # Wrap in full HTML for browser preview
    full_html = preview_html(result.html, theme)

    # Write to temp file
    input_path = Path(args.input)
    output = args.output or str(input_path.with_suffix(".html"))
    Path(output).write_text(full_html, encoding="utf-8")

    print(f"Title: {result.title}")
    print(f"Digest: {result.digest}")
    print(f"Images: {len(result.images)}")
    print(f"Output: {output}")

    if not args.no_open:
        webbrowser.open(f"file://{Path(output).absolute()}")
        print("Opened in browser.")


def cmd_export(args):
    """Export article to platform-specific files."""
    md_content = Path(args.input).read_text(encoding="utf-8")
    theme_name = args.theme or load_config().get("theme", "professional-clean")
    images_dir = args.images

    if args.platform == "all":
        results = export_all_platforms(md_content, args.output, theme_name, images_dir)
        
        # Generate usage guide
        readme_path = generate_usage_guide(args.output, results, images_dir)
        
        # Generate HTML preview pages
        gallery_path = generate_image_gallery_html(args.output, images_dir)
        preview_path = generate_file_preview_html(args.output, results, images_dir)
        
        # Display all files in a nice table format
        print(f"\n✅ 导出完成！共 {len(results)} 个平台")
        print(f"📂 输出目录: {args.output}\n")
        
        print("📋 文件清单:")
        print("-" * 70)
        total_files = 0
        for platform, files in results.items():
            platform_name = PLATFORM_DISPLAY_NAMES.get(platform, platform)
            file_list = []
            for fmt, path in files.items():
                if fmt == "images":
                    continue
                file_list.append(Path(path).name)
                total_files += 1
            print(f"  [{platform_name}] {', '.join(file_list)}")
        print("-" * 70)
        print(f"共计 {total_files} 个文件\n")
        
        # Show images
        if images_dir:
            images_path = Path(images_dir)
            if images_path.exists():
                imgs = [f for f in images_path.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
                if imgs:
                    print("🖼️ 配图文件:")
                    for img in sorted(imgs):
                        print(f"  - {img.name}")
                    print(f"共计 {len(imgs)} 张配图\n")
        
        # Show readme
        print(f"📖 使用说明: {readme_path}")
        if preview_path:
            print(f"🌐 文件预览: {preview_path}")
        if gallery_path:
            print(f"🖼️ 图片预览: {gallery_path}")
        print()
        
    else:
        results = export_platform(md_content, args.platform, args.output, theme_name, images_dir)
        platform_name = PLATFORM_DISPLAY_NAMES.get(args.platform, args.platform)
        print(f"\n✅ 导出完成: [{platform_name}]")
        print(f"📂 输出目录: {args.output}\n")
        for fmt, path in results.items():
            if fmt != "images":
                print(f"  {fmt}: {Path(path).name}")
        print()


def cmd_per_platform(args):
    """Generate unique articles and images for each platform based on the same topic."""
    topic = args.topic
    platforms = args.platforms.split(",") if args.platforms else list(PLATFORM_SPECS.keys())
    framework = args.framework or "对比"
    output_dir = args.output or Path.cwd() / "output" / f"per-platform-{Path(topic).stem}"
    output_dir = str(Path(output_dir))
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    config = load_config()

    print(f"🎯 主题: {topic}")
    print(f"📱 平台: {', '.join(platforms)}")
    print(f"📐 框架: {framework}")
    print(f"📂 输出: {output_dir}")
    print()

    # Step 1: Check if articles exist in output directory
    print("Step 1/4: 检查各平台文章...")
    articles = {}
    for platform in platforms:
        article_path = Path(output_dir) / f"{platform}.md"
        if article_path.exists():
            article = article_path.read_text(encoding="utf-8")
            articles[platform] = article
            title = ""
            for line in article.split("\n")[:5]:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            print(f"  ✅ {platform}: ~{len(article)} 字, 标题: {title[:25]}...（已存在）")
        else:
            articles[platform] = None
            print(f"  ⏳ {platform}: 待生成")

    # Check if any articles need to be written by AI assistant
    pending = [p for p, a in articles.items() if a is None]
    if pending:
        print()
        print("⚠️  以下平台文章待 AI 助手生成（请在对话中完成）：")
        for p in pending:
            platform_name = PLATFORM_DISPLAY_NAMES.get(p, p)
            spec = PLATFORM_SPECS.get(p, "")
            # Extract key requirements
            word_count = "1200-2000"
            style = "专业干货"
            for line in spec.split("\n"):
                m2 = re.match(r"-\s*字数[：:]\s*(.+)", line)
                if m2:
                    word_count = m2.group(1).strip()
                m3 = re.match(r"-\s*风格[：:]\s*(.+)", line)
                if m3:
                    style = m3.group(1).strip()
            print(f"\n📝 [{platform_name}]")
            print(f"  字数：{word_count} 字")
            print(f"  风格：{style}")
            print(f"  框架：{framework}")
            print(f"  保存路径：{output_dir}/{p}.md")
        print()
        print("=" * 70)
        print("请 AI 助手为每个待生成平台独立撰写文章，保存到对应路径。")
        print("完成后重新运行此命令以继续。")
        return

    # Step 2: Generate per-platform images
    print("Step 2/4: 为每个平台生成独立配图...")
    platform_images = {}
    for platform, article in articles.items():
        print(f"  [{platform}] 生成配图...")
        try:
            imgs = generate_platform_images(platform, article, output_dir, config)
            platform_images[platform] = imgs
        except Exception as e:
            print(f"  ⚠️ [{platform}] 图片生成失败: {e}")
            platform_images[platform] = {}
    print()

    # Step 3: Export each platform's article + images
    print("Step 3/4: 导出各平台文件...")
    theme_name = args.theme or load_config().get("theme", "professional-clean")
    results = {}
    for platform, article in articles.items():
        print(f"  [{platform}] 导出...")
        imgs = platform_images.get(platform, {})
        images_dir = str(Path(output_dir) / platform) if imgs else None
        
        platform_results = export_platform(article, platform, output_dir, theme_name, images_dir)
        # Merge images
        if imgs:
            platform_results["images"] = {k: v for k, v in imgs.items()}
        results[platform] = platform_results

    # Step 4: Generate usage guide and previews
    print("Step 4/4: 生成HTML预览页面...")
    readme_path = generate_usage_guide(output_dir, results)
    gallery_path = generate_image_gallery_html(output_dir)
    preview_path = generate_file_preview_html(output_dir, results)

    print()
    print(f"✅ 每平台独立生成完成！共 {len(results)} 个平台")
    print(f"📂 输出目录: {output_dir}\n")

    print("📋 文件清单:")
    print("-" * 70)
    total_files = 0
    total_images = 0
    for platform, files in results.items():
        platform_name = PLATFORM_DISPLAY_NAMES.get(platform, platform)
        file_list = []
        for fmt, path in files.items():
            if fmt == "images":
                if isinstance(path, dict):
                    img_count = len(path)
                    total_images += img_count
                    file_list.append(f"{img_count} 张图片")
                continue
            file_list.append(Path(path).name)
            total_files += 1
        print(f"  [{platform_name}] {', '.join(file_list)}")
    print("-" * 70)
    print(f"共计 {total_files} 个文件，{total_images} 张配图\n")

    if readme_path:
        print(f"📖 使用说明: {readme_path}")
    if preview_path:
        print(f"🌐 文件预览: {preview_path}")
    if gallery_path:
        print(f"🖼️ 图片预览: {gallery_path}")
    print()


def cmd_themes(args):
    """List available themes."""
    names = list_themes()
    for name in names:
        theme = load_theme(name)
        print(f"  {name:24s} {theme.description}")


def cmd_gallery(args):
    """Render all themes side by side in a browser gallery."""
    from concurrent.futures import ThreadPoolExecutor

    # Use provided markdown or a built-in sample
    if args.input:
        md_text = Path(args.input).read_text(encoding="utf-8")
    else:
        md_text = _gallery_sample_markdown()

    names = list_themes()
    results = {}

    def render_theme(name):
        theme = load_theme(name)
        converter = WeChatConverter(theme=theme)
        result = converter.convert(md_text)
        return name, theme.description, result.html

    # Parallel rendering
    with ThreadPoolExecutor(max_workers=8) as pool:
        for name, desc, html in pool.map(lambda n: render_theme(n), names):
            results[name] = (desc, html)

    # Build gallery HTML
    gallery_html = _build_gallery_html(results, names)
    output = args.output or "/tmp/writer-gallery.html"
    Path(output).write_text(gallery_html, encoding="utf-8")
    print(f"Gallery: {output} ({len(names)} themes)")

    if not args.no_open:
        webbrowser.open(f"file://{Path(output).absolute()}")


def cmd_learn_theme(args):
    """Learn a theme from a WeChat article URL."""
    import subprocess
    script = Path(__file__).parent.parent / "scripts" / "learn_theme.py"
    cmd = [sys.executable, str(script), args.url, "--name", args.name]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def _gallery_sample_markdown():
    return """# 示例文章标题

## 第一部分

这是一段正常的文章内容，用来展示不同主题的排版效果。Writer 支持多种排版主题，每种都有独特的视觉风格。

说实话，选主题这件事——看截图永远不如看实际渲染效果。

## 关键数据

| 指标 | 数值 | 变化 |
|------|------|------|
| 阅读量 | 12,580 | +23% |
| 分享率 | 4.7% | +0.8% |
| 完读率 | 68% | -2% |

## 代码示例

```python
def hello():
    print("Hello, Writer!")
```

> 好的排版不是让读者注意到设计，而是让读者忘记设计，只记住内容。

## 列表展示

- 第一个要点：简洁是设计的灵魂
- 第二个要点：一致性比创意更重要
- 第三个要点：移动端体验优先

**加粗文本**和*斜体文本*的样式也需要关注。

最后这段用来展示文章结尾的留白和间距效果。一篇好文章的结尾，应该像一首好歌的最后一个音符——恰到好处地收束。
"""


def _join_newline(items):
    """Join items with comma + newline (workaround for f-string limitation)."""
    return ",\n".join(items)


def _build_gallery_html(results, names):
    cards = []
    for name in names:
        desc, html = results[name]
        # Escape for embedding in JS
        escaped_html = html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
        cards.append(f"""
        <div class="theme-card" onclick="selectTheme('{name}')">
          <div class="theme-name">{name}</div>
          <div class="theme-desc">{desc}</div>
          <div class="phone-frame">
            <div class="phone-content" id="preview-{name}">{html}</div>
          </div>
          <button class="copy-btn" onclick="event.stopPropagation(); copyHTML('{name}')">复制 HTML</button>
        </div>""")

    # Store HTML data for copy
    data_entries = []
    for name in names:
        desc, html = results[name]
        safe = html.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
        data_entries.append(f"  '{name}': '{safe}'")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Writer 主题画廊</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f0f0f; color: #fff; }}
.header {{ text-align: center; padding: 40px 20px 20px; }}
.header h1 {{ font-size: 28px; font-weight: 700; }}
.header p {{ color: #888; margin-top: 8px; font-size: 15px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 24px; padding: 24px; max-width: 1440px; margin: 0 auto; }}
.theme-card {{ background: #1a1a1a; border-radius: 12px; padding: 16px; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }}
.theme-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }}
.theme-name {{ font-size: 16px; font-weight: 700; margin-bottom: 4px; }}
.theme-desc {{ font-size: 13px; color: #888; margin-bottom: 12px; }}
.phone-frame {{ background: #fff; border-radius: 8px; overflow: hidden; max-height: 480px; overflow-y: auto; }}
.phone-content {{ padding: 16px; font-size: 14px; transform: scale(0.85); transform-origin: top left; width: 118%; }}
.copy-btn {{ margin-top: 12px; width: 100%; padding: 8px; background: #333; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }}
.copy-btn:hover {{ background: #555; }}
.toast {{ position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%); background: #333; color: #fff; padding: 10px 24px; border-radius: 8px; font-size: 14px; display: none; z-index: 999; }}
</style>
</head>
<body>
<div class="header">
  <h1>Writer 主题画廊</h1>
  <p>{len(names)} 个主题 · 点击卡片查看大图 · 点击「复制 HTML」直接粘贴到公众号编辑器</p>
</div>
<div class="grid">
{''.join(cards)}
</div>
<div class="toast" id="toast">已复制到剪贴板</div>
<script>
const themeData = {{
{_join_newline(data_entries)}
}};
function copyHTML(name) {{
  const html = themeData[name];
  if (html) {{
    navigator.clipboard.writeText(html).then(() => {{
      const t = document.getElementById('toast');
      t.style.display = 'block';
      setTimeout(() => t.style.display = 'none', 1500);
    }});
  }}
}}
function selectTheme(name) {{
  localStorage.setItem('writer-theme', name);
  // Scroll to card for visual feedback
  const el = document.getElementById('preview-' + name);
  if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
}}
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        prog="writer",
        description="Multi-platform content exporter (HTML/Markdown/Word + images)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # preview
    p_preview = sub.add_parser("preview", help="Generate HTML and open in browser")
    p_preview.add_argument("input", help="Markdown file path")
    p_preview.add_argument("-t", "--theme", default="professional-clean", help="Theme name")
    p_preview.add_argument("-o", "--output", help="Output HTML file path")
    p_preview.add_argument("--no-open", action="store_true", help="Don't open browser")

    # export
    p_export = sub.add_parser("export", help="Export to platform-specific files")
    p_export.add_argument("input", help="Markdown file path")
    p_export.add_argument("--platform", required=True, help="Target platform or 'all'")
    p_export.add_argument("--output", required=True, help="Output directory")
    p_export.add_argument("-t", "--theme", default=None, help="Theme name")
    p_export.add_argument("--images", help="Images directory to copy")

    # per-platform (new mode)
    p_per = sub.add_parser("per-platform", help="Generate unique articles + images for each platform")
    p_per.add_argument("topic", help="Article topic")
    p_per.add_argument("--platforms", default=None,
                       help="Comma-separated platform keys (default: all)")
    p_per.add_argument("--framework", default="对比", help="Writing framework")
    p_per.add_argument("--output", default=None, help="Output directory")
    p_per.add_argument("-t", "--theme", default=None, help="Theme name")

    # themes
    sub.add_parser("themes", help="List available themes")

    # gallery
    p_gallery = sub.add_parser("gallery", help="Open theme gallery in browser")
    p_gallery.add_argument("input", nargs="?", default=None, help="Markdown file (optional, uses sample if omitted)")
    p_gallery.add_argument("-o", "--output", help="Output HTML file path")
    p_gallery.add_argument("--no-open", action="store_true", help="Don't open browser")

    # learn-theme
    p_learn = sub.add_parser("learn-theme", help="Learn formatting theme from a WeChat article URL")
    p_learn.add_argument("url", help="WeChat article URL")
    p_learn.add_argument("--name", required=True, help="Theme name")

    args = parser.parse_args()

    try:
        if args.command == "preview":
            cmd_preview(args)
        elif args.command == "export":
            cmd_export(args)
        elif args.command == "per-platform":
            cmd_per_platform(args)
        elif args.command == "themes":
            cmd_themes(args)
        elif args.command == "gallery":
            cmd_gallery(args)
        elif args.command == "learn-theme":
            cmd_learn_theme(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
