#!/usr/bin/env python3
"""
Multi-platform file exporter for Writer.

Exports articles to platform-specific formats (HTML/Markdown/Word) with images.

Usage:
    python exporter.py export article.md --platform wechat --output ./output/2026-05-09-article/
    python exporter.py export article.md --platform all --output ./output/2026-05-09-article/
"""

import sys
import json
from pathlib import Path
from io import BytesIO

import yaml

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from converter import WeChatConverter, preview_html
from theme import load_theme

# Platform display names for file naming
PLATFORM_DISPLAY_NAMES = {
    "wechat": "公众号",
    "xiaohongshu": "小红书",
    "zhihu": "知乎",
    "baijiahao": "百家号",
    "weibo": "微博",
    "sohu": "搜狐",
    "toutiao": "今日头条",
    "qiehao": "企鹅号",
    "jianshu": "简书",
    "douban": "豆瓣",
    "dayu": "大鱼号",
    "kr36": "36氪",
    "bilibili": "B站",
    "douyin": "抖音",
    "newsletter": "Newsletter",
}

SUPPORTED_PLATFORMS = [
    "wechat", "xiaohongshu", "zhihu", "baijiahao",
    "weibo", "sohu", "toutiao", "qiehao",
    "jianshu", "douban", "dayu", "kr36",
]

PLATFORM_FORMATS = {
    "wechat": "html",
    "xiaohongshu": "md",
    "zhihu": "md",
    "baijiahao": "html",
    "weibo": "md",
    "sohu": "html",
    "toutiao": "html",
    "qiehao": "html",
    "jianshu": "md",
    "douban": "md",
    "dayu": "html",
    "kr36": "md",
}

CONFIG_PATHS = [
    Path.cwd() / "config.yaml",
    Path(__file__).parent.parent / "config.yaml",
    Path(__file__).parent / "config.yaml",
    Path.home() / ".config" / "writer" / "config.yaml",
]


def _load_config() -> dict:
    for p in CONFIG_PATHS:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


def _load_style() -> dict:
    for p in [Path.cwd() / "style.yaml", Path(__file__).parent.parent / "style.yaml"]:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


def _convert_to_html(md_content: str, theme_name: str = "professional-clean") -> str:
    """Convert Markdown to WeChat-compatible HTML with inline styles."""
    theme = load_theme(theme_name)
    converter = WeChatConverter(theme=theme)
    result = converter.convert(md_content)
    return preview_html(result.html, theme)


def _convert_to_standard_html(md_content: str) -> str:
    """Convert Markdown to standard HTML without WeChat-specific fixes."""
    import markdown
    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "codehilite", "toc"],
        output_format="html"
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; line-height: 1.8; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
h1 {{ font-size: 24px; margin-top: 2em; }}
h2 {{ font-size: 20px; margin-top: 1.5em; }}
h3 {{ font-size: 18px; margin-top: 1.2em; }}
p {{ margin: 1em 0; }}
img {{ max-width: 100%; height: auto; display: block; margin: 1em auto; }}
blockquote {{ border-left: 4px solid #ddd; padding-left: 16px; color: #666; margin: 1em 0; }}
code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
pre {{ background: #f5f5f5; padding: 16px; border-radius: 6px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
th {{ background: #f5f5f5; font-weight: 600; }}
a {{ color: #1a73e8; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
ul, ol {{ padding-left: 2em; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""


def _process_markdown_for_platform(md_content: str, platform: str) -> str:
    """Process Markdown content for specific platform requirements."""
    if platform == "xiaohongshu":
        processed = _optimize_for_xiaohongshu(md_content)
    elif platform == "weibo":
        processed = _optimize_for_weibo(md_content)
    elif platform == "jianshu":
        processed = md_content
    elif platform == "douban":
        processed = md_content
    elif platform == "zhihu":
        processed = md_content
    elif platform == "kr36":
        processed = md_content
    else:
        processed = md_content
    return processed


def _optimize_for_xiaohongshu(md_content: str) -> str:
    """Optimize content for Xiaohongshu: emoji, short paragraphs, tags."""
    import re

    lines = md_content.split("\n")
    result_lines = []
    for line in lines:
        if line.startswith("# "):
            title = line[2:]
            result_lines.append(f"# {title}")
            result_lines.append("")
        elif line.startswith("## "):
            heading = line[3:]
            emoji = _get_section_emoji(heading)
            result_lines.append(f"## {emoji} {heading}")
            result_lines.append("")
        elif line.strip() and not line.startswith("#") and not line.startswith("-") and not line.startswith(">"):
            if line.strip().startswith("!["):
                result_lines.append("")
                result_lines.append(line)
                result_lines.append("")
            else:
                result_lines.append(line)
                result_lines.append("")
        else:
            result_lines.append(line)

    return "\n".join(result_lines)


def _get_section_emoji(heading: str) -> str:
    emoji_map = {
        "总结": "✨", "前言": "📌", "推荐": "🌟", "测评": "📊",
        "对比": "⚖️", "教程": "📝", "经验": "💡", "避坑": "⚠️",
        "工具": "🛠️", "方法": "🔧", "技巧": "💫", "建议": "✅",
        "注意": "🔥", "重点": "❗", "福利": "🎁", "案例": "📋",
    }
    for keyword, emoji in emoji_map.items():
        if keyword in heading:
            return emoji
    return "📖"


def _optimize_for_weibo(md_content: str) -> str:
    """Optimize content for Weibo: add hashtags, keep it short."""
    import re

    first_line = md_content.split("\n")[0]
    if first_line.startswith("# "):
        title = first_line[2:]
        hashtag = f"#{title.replace(' ', '')}#"
        md_content = md_content.replace(first_line, f"{hashtag}\n\n{title}", 1)

    return md_content


def _generate_word_from_html(html_content: str, output_path: str):
    """Generate Word document from HTML content."""
    from bs4 import BeautifulSoup
    import markdown

    soup = BeautifulSoup(html_content, "html.parser")

    doc = Document()

    doc.styles["Normal"].font.name = "微软雅黑"
    doc.styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    doc.styles["Normal"].font.size = Pt(12)
    doc.styles["Normal"].paragraph_format.space_after = Pt(6)
    doc.styles["Normal"].paragraph_format.line_spacing = 1.5

    heading_styles = {
        "h1": {"size": Pt(22), "bold": True, "color": RGBColor(0x1A, 0x1A, 0x1A), "space_before": Pt(18), "space_after": Pt(12)},
        "h2": {"size": Pt(18), "bold": True, "color": RGBColor(0x33, 0x33, 0x33), "space_before": Pt(14), "space_after": Pt(8)},
        "h3": {"size": Pt(15), "bold": True, "color": RGBColor(0x4D, 0x4D, 0x4D), "space_before": Pt(12), "space_after": Pt(6)},
        "h4": {"size": Pt(14), "bold": True, "color": RGBColor(0x4D, 0x4D, 0x4D), "space_before": Pt(10), "space_after": Pt(6)},
    }

    for element in soup.find_all(True):
        tag = element.name.lower()

        if tag in heading_styles:
            style = heading_styles[tag]
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = style["space_before"]
            p.paragraph_format.space_after = style["space_after"]
            run = p.add_run(element.get_text())
            run.font.size = style["size"]
            run.bold = style["bold"]
            run.font.color.rgb = style["color"]
            run.font.name = "微软雅黑"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

        elif tag == "p":
            if not element.get_text().strip():
                continue
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.5
            _add_formatted_runs(p, element)

        elif tag in ("ul", "ol"):
            for i, li in enumerate(element.find_all("li", recursive=False)):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(1.5)
                p.paragraph_format.space_after = Pt(4)
                prefix = f"{i + 1}. " if tag == "ol" else "• "
                run = p.add_run(prefix)
                run.font.name = "微软雅黑"
                run.font.size = Pt(12)
                _add_formatted_runs(p, li)

        elif tag == "blockquote":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(element.get_text())
            run.italic = True
            run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            run.font.name = "微软雅黑"
            run.font.size = Pt(12)
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

        elif tag == "img":
            img_src = element.get("src", "")
            if img_src and not img_src.startswith(("http://", "https://")):
                img_path = Path(img_src)
                if img_path.exists():
                    doc.add_picture(str(img_path), width=Inches(5))

        elif tag == "table":
            rows = element.find_all("tr")
            if rows:
                header_cells = rows[0].find_all(["th", "td"])
                table = doc.add_table(rows=len(rows), cols=len(header_cells))
                table.style = "Light Grid Accent 1"
                for i, tr in enumerate(rows):
                    for j, cell in enumerate(tr.find_all(["th", "td"])):
                        table_cell = table.cell(i, j)
                        table_cell.text = cell.get_text().strip()
                        if i == 0:
                            for paragraph in table_cell.paragraphs:
                                for run in paragraph.runs:
                                    run.bold = True

        elif tag == "hr":
            doc.add_paragraph()

        elif tag == "br":
            pass

        elif tag == "strong" or tag == "b":
            if element.parent and element.parent.name not in ("p", "li", "td", "th"):
                p = doc.add_paragraph()
                run = p.add_run(element.get_text())
                run.bold = True
                run.font.name = "微软雅黑"
                run.font.size = Pt(12)

        elif tag == "em" or tag == "i":
            if element.parent and element.parent.name not in ("p", "li", "td", "th"):
                p = doc.add_paragraph()
                run = p.add_run(element.get_text())
                run.italic = True
                run.font.name = "微软雅黑"
                run.font.size = Pt(12)

        elif tag == "pre":
            code_text = element.get_text()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(code_text)
            run.font.name = "Consolas"
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output))


def _add_formatted_runs(paragraph, element):
    """Add formatted text runs to a Word paragraph from HTML element."""
    for child in element.children:
        if hasattr(child, "name"):
            if child.name == "strong" or child.name == "b":
                run = paragraph.add_run(child.get_text())
                run.bold = True
            elif child.name == "em" or child.name == "i":
                run = paragraph.add_run(child.get_text())
                run.italic = True
            elif child.name == "a":
                run = paragraph.add_run(child.get_text())
                run.font.color.rgb = RGBColor(0x1A, 0x73, 0xE8)
            elif child.name == "img":
                img_src = child.get("src", "")
                if img_src and not img_src.startswith(("http://", "https://")):
                    img_path = Path(img_src)
                    if img_path.exists():
                        paragraph.add_run()
                        try:
                            paragraph.runs[-1].add_picture(str(img_path), width=Inches(4))
                        except Exception:
                            pass
            elif child.name == "br":
                paragraph.add_run("\n")
            else:
                paragraph.add_run(child.get_text())
        else:
            text = str(child)
            if text.strip():
                paragraph.add_run(text)

    if not element.children:
        run = paragraph.add_run(element.get_text())
        run.font.name = "微软雅黑"
        run.font.size = Pt(12)
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def _generate_word_from_md(md_content: str, output_path: str):
    """Generate Word document directly from Markdown content."""
    import markdown
    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "codehilite", "toc"],
        output_format="html"
    )
    full_html = f"<html><body>{html_body}</body></html>"
    _generate_word_from_html(full_html, output_path)


def export_platform(md_content: str, platform: str, output_dir: str, theme_name: str = "professional-clean", images_dir: str = None):
    """Export content for a single platform.

    Args:
        md_content: Source Markdown content
        platform: Target platform name
        output_dir: Output directory path
        theme_name: Theme name for HTML conversion
        images_dir: Images directory path (copied to output)

    Returns:
        dict with exported file paths
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    files = {}
    platform_name = PLATFORM_DISPLAY_NAMES.get(platform, platform)
    base_name = f"{platform_name}-{platform}"

    processed_md = _process_markdown_for_platform(md_content, platform)

    md_path = output / f"{base_name}.md"
    md_path.write_text(processed_md, encoding="utf-8")
    files["md"] = str(md_path)

    if platform in PLATFORM_FORMATS and PLATFORM_FORMATS[platform] == "html":
        if platform == "wechat":
            html_content = _convert_to_html(processed_md, theme_name)
        else:
            html_content = _convert_to_standard_html(processed_md)
        html_path = output / f"{base_name}.html"
        html_path.write_text(html_content, encoding="utf-8")
        files["html"] = str(html_path)

    docx_path = output / f"{base_name}.docx"
    if platform in PLATFORM_FORMATS and PLATFORM_FORMATS[platform] == "html":
        html_content = files.get("html")
        if html_content:
            _generate_word_from_html(Path(html_content).read_text(encoding="utf-8"), str(docx_path))
        else:
            _generate_word_from_md(processed_md, str(docx_path))
    else:
        _generate_word_from_md(processed_md, str(docx_path))
    files["docx"] = str(docx_path)

    if images_dir:
        images_src = Path(images_dir)
        images_dst = output / "images"
        if images_src.exists():
            import shutil
            if images_src.resolve() == images_dst.resolve():
                files["images"] = str(images_dst)
            else:
                if images_dst.exists():
                    shutil.rmtree(images_dst)
                shutil.copytree(images_src, images_dst)
                files["images"] = str(images_dst)

    return files


def generate_usage_guide(output_dir: str, platform_files: dict, images_dir: str = None):
    """Generate an HTML usage guide for exported files."""
    output = Path(output_dir)
    
    platform_instructions = {
        "wechat": {
            "desc": "微信公众号文章",
            "usage": "复制 HTML 内容到微信公众平台编辑器，图片需手动上传",
            "cover_ratio": "2.35:1",
        },
        "xiaohongshu": {
            "desc": "小红书笔记",
            "usage": "复制文字内容，配合 3:4 封面图发布",
            "cover_ratio": "3:4",
        },
        "zhihu": {
            "desc": "知乎文章/回答",
            "usage": "复制 Markdown 内容到知乎编辑器",
            "cover_ratio": "16:9",
        },
        "baijiahao": {
            "desc": "百度百家号文章",
            "usage": "复制 HTML 内容到百家号编辑器",
            "cover_ratio": "16:9",
        },
        "weibo": {
            "desc": "微博长文",
            "usage": "复制文字内容，配图发布（字数超限时使用头条文章）",
            "cover_ratio": "1:1",
        },
        "sohu": {
            "desc": "搜狐号文章",
            "usage": "复制 HTML 内容到搜狐号编辑器",
            "cover_ratio": "16:9",
        },
        "toutiao": {
            "desc": "今日头条文章",
            "usage": "复制 HTML 内容到头条号编辑器",
            "cover_ratio": "16:9",
        },
        "qiehao": {
            "desc": "企鹅号（腾讯新闻）文章",
            "usage": "复制 HTML 内容到企鹅号编辑器",
            "cover_ratio": "16:9",
        },
        "jianshu": {
            "desc": "简书文章",
            "usage": "复制 Markdown 内容到简书编辑器",
            "cover_ratio": "16:9",
        },
        "douban": {
            "desc": "豆瓣文章/日记",
            "usage": "复制文字内容到豆瓣编辑器",
            "cover_ratio": "16:9",
        },
        "dayu": {
            "desc": "大鱼号（UC）文章",
            "usage": "复制 HTML 内容到大鱼号编辑器",
            "cover_ratio": "16:9",
        },
        "kr36": {
            "desc": "36氪文章",
            "usage": "复制 Markdown 内容到36氪投稿系统",
            "cover_ratio": "16:9",
        },
        "bilibili": {
            "desc": "B站视频脚本/专栏",
            "usage": "按脚本录制视频，或作为专栏文章发布",
            "cover_ratio": "16:9",
        },
        "douyin": {
            "desc": "抖音短视频脚本",
            "usage": "按脚本拍摄短视频，配合文案发布",
            "cover_ratio": "9:16",
        },
        "newsletter": {
            "desc": "Newsletter 邮件",
            "usage": "发送 HTML 邮件，或复制文字内容到邮件平台",
            "cover_ratio": "N/A",
        },
    }
    
    format_map = {"md": "Markdown", "html": "HTML", "docx": "Word"}
    format_class = {"md": "format-md", "html": "format-html", "docx": "format-docx"}
    
    # Build platform rows
    platform_rows = []
    for platform, files in platform_files.items():
        info = platform_instructions.get(platform, {"desc": platform, "usage": ""})
        files_list = []
        for fmt, fpath in files.items():
            if fmt == "images":
                continue
            fname = Path(fpath).name
            fmt_label = format_map.get(fmt, fmt.upper())
            fmt_cls = format_class.get(fmt, "format-md")
            if fmt == "docx":
                files_list.append(f'<a href="{fname}" class="format-badge {fmt_cls}" download>{fname}</a>')
            else:
                files_list.append(f'<a href="{fname}" class="format-badge {fmt_cls}" target="_blank">{fname}</a>')
        files_str = " ".join(files_list)
        platform_rows.append(f"""<tr>
            <td>{info['desc']}</td>
            <td>{files_str}</td>
            <td>{info['usage']}</td>
        </tr>""")
    
    # Build image rows
    image_rows = []
    if images_dir:
        images_path = Path(images_dir)
        if images_path.exists():
            for img in sorted(images_path.iterdir()):
                if img.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                    image_rows.append(f"""<tr>
                        <td><img src="images/{img.name}" alt="{img.name}" style="max-width: 100px; max-height: 60px; border-radius: 4px; cursor: pointer;" onclick="window.open('images/{img.name}', '_blank')"></td>
                        <td>{img.name}</td>
                        <td>{img.name.replace('_', ' ')}</td>
                    </tr>""")
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件使用说明</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 40px 20px;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ font-size: 24px; margin-bottom: 8px; color: #1a1a1a; }}
        .subtitle {{ color: #666; margin-bottom: 24px; font-size: 14px; }}
        h2 {{ font-size: 18px; margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 2px solid #007bff; color: #1a1a1a; }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 24px;
        }}
        th {{ background: #007bff; color: white; padding: 12px 16px; text-align: left; font-weight: 500; }}
        td {{ padding: 10px 16px; border-bottom: 1px solid #eee; vertical-align: top; }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover {{ background: #f8f9fa; }}
        .format-badge {{
            display: inline-block;
            padding: 2px 8px;
            background: #e9ecef;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            color: #495057;
            margin: 2px;
            text-decoration: none;
            transition: opacity 0.2s;
        }}
        .format-badge:hover {{ opacity: 0.75; text-decoration: underline; }}
        .format-html {{ background: #cce5ff; color: #004085; }}
        .format-md {{ background: #d4edda; color: #155724; }}
        .format-docx {{ background: #fff3cd; color: #856404; }}
        .nav-links {{
            display: flex;
            gap: 12px;
            margin: 16px 0 24px;
        }}
        .nav-link {{
            display: inline-block;
            padding: 10px 20px;
            background: white;
            border: 2px solid #007bff;
            color: #007bff;
            text-decoration: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        .nav-link:hover {{
            background: #007bff;
            color: white;
            text-decoration: none;
        }}
        .tip {{
            background: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 12px 16px;
            margin: 24px 0;
            border-radius: 0 8px 8px 0;
            font-size: 14px;
            color: #004085;
        }}
        .tip ol {{ margin-left: 20px; margin-top: 8px; }}
        .tip li {{ margin: 4px 0; }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 13px;
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📂 文件使用说明</h1>
        <p class="subtitle">本文档说明本次导出的所有文件及其用途。</p>

        <div class="nav-links">
            <a href="文件清单_可点击预览.html" class="nav-link">📄 文件清单（预览/下载）</a>
            <a href="图片清单.html" class="nav-link">🖼️ 图片清单（预览/下载）</a>
        </div>

        <h2>📋 文件清单</h2>
        <table>
            <thead>
                <tr>
                    <th>平台</th>
                    <th>文件</th>
                    <th>用途说明</th>
                </tr>
            </thead>
            <tbody>
                {''.join(platform_rows)}
            </tbody>
        </table>

        {'<h2>🖼️ 配图文件</h2><table><thead><tr><th>缩略图</th><th>文件名</th><th>说明</th></tr></thead><tbody>' + ''.join(image_rows) + '</tbody></table>' if image_rows else ''}

        <div class="tip">
            <strong>💡 发布提示</strong>
            <ol>
                <li><strong>HTML 文件</strong>：直接复制全部内容到对应平台的富文本编辑器</li>
                <li><strong>Markdown 文件</strong>：复制文字内容到平台编辑器（部分平台支持 Markdown）</li>
                <li><strong>Word 文件</strong>：可用 Word 打开查看，或用于需要上传文档的场景</li>
                <li><strong>图片</strong>：需要手动上传到对应平台，然后插入文章中</li>
                <li><strong>视频脚本</strong>：按脚本标注的分镜和时间拍摄视频</li>
            </ol>
        </div>

        <div class="footer">由 Writer 自动生成</div>
    </div>
</body>
</html>"""
    
    readme_path = output / "README_文件说明.html"
    readme_path.write_text(html_content, encoding="utf-8")
    
    # Keep MD version for backward compatibility
    md_path = output / "README_文件说明.md"
    md_lines = [
        "# 📂 文件使用说明",
        "",
        "本文档说明本次导出的所有文件及其用途。",
        "",
        "👉 请查看 [README_文件说明.html](./README_文件说明.html) 获取可视化使用说明。",
        "",
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    
    return str(readme_path)


def generate_image_gallery_html(output_dir: str, images_dir: str = None):
    """Generate an HTML image gallery for preview."""
    output = Path(output_dir)
    if not images_dir:
        images_dir = output / "images"
    images_path = Path(images_dir)
    
    images = []
    if images_path.exists():
        for img in sorted(images_path.iterdir()):
            if img.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                images.append({
                    "name": img.name,
                    "src": f"images/{img.name}",
                    "type": "封面" if "cover" in img.name else "配图",
                })
    
    if not images:
        # Even without images, generate an empty gallery page
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图片清单</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 40px 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ font-size: 24px; margin-bottom: 24px; color: #1a1a1a; }}
        .nav-links {{
            display: flex;
            gap: 12px;
            margin: 16px 0 24px;
        }}
        .nav-link {{
            display: inline-block;
            padding: 10px 20px;
            background: white;
            border: 2px solid #007bff;
            color: #007bff;
            text-decoration: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        .nav-link:hover {{ background: #007bff; color: white; text-decoration: none; }}
        .empty {{ text-align: center; padding: 60px 20px; color: #999; font-size: 16px; background: white; border-radius: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📸 图片清单</h1>
        <div class="nav-links">
            <a href="README_文件说明.html" class="nav-link">📂 文件说明</a>
            <a href="文件清单_可点击预览.html" class="nav-link">📄 文件清单</a>
        </div>
        <div class="empty">暂无图片文件。图片生成服务不可用，可手动生成后重新运行导出。</div>
    </div>
</body>
</html>"""
        gallery_path = output / "图片清单.html"
        gallery_path.write_text(html_content, encoding="utf-8")
        return str(gallery_path)
    
    cards_html = []
    for img in images:
        card = f"""
        <div class="image-card">
            <img src="{img['src']}" alt="{img['name']}" onclick="window.open(this.src, '_blank')">
            <div class="image-info">
                <span class="label">文件名</span>
                <span class="value">{img['name']}</span>
            </div>
            <a href="{img['src']}" class="download-btn" download>预览 / 下载原图</a>
        </div>"""
        cards_html.append(card)
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图片清单</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 40px 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ font-size: 24px; margin-bottom: 24px; color: #1a1a1a; }}
        h2 {{ font-size: 18px; margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 2px solid #007bff; color: #1a1a1a; }}
        .image-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .image-card img {{
            width: 100%;
            max-height: 400px;
            object-fit: contain;
            border-radius: 8px;
            margin-bottom: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .image-card img:hover {{ transform: scale(1.02); }}
        .image-info {{
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 8px 16px;
            font-size: 14px;
        }}
        .image-info .label {{ color: #666; font-weight: 500; }}
        .image-info .value {{ color: #333; }}
        .download-btn {{
            display: inline-block;
            margin-top: 12px;
            padding: 8px 16px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            transition: background 0.2s;
        }}
        .download-btn:hover {{ background: #0056b3; }}
        .nav-links {{
            display: flex;
            gap: 12px;
            margin: 16px 0 24px;
        }}
        .nav-link {{
            display: inline-block;
            padding: 10px 20px;
            background: white;
            border: 2px solid #007bff;
            color: #007bff;
            text-decoration: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        .nav-link:hover {{ background: #007bff; color: white; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📸 图片清单</h1>
        <div class="nav-links">
            <a href="README_文件说明.html" class="nav-link">📂 文件说明</a>
            <a href="文件清单_可点击预览.html" class="nav-link">📄 文件清单</a>
        </div>
        <h2>全部图片 ({len(images)} 张)</h2>
        {''.join(cards_html)}
    </div>
</body>
</html>"""
    
    gallery_path = output / "图片清单.html"
    gallery_path.write_text(html_content, encoding="utf-8")
    return str(gallery_path)


def generate_file_preview_html(output_dir: str, platform_files: dict, images_dir: str = None):
    """Generate an HTML file preview page with thumbnails and download links."""
    output = Path(output_dir)
    
    platform_info_map = {
        "wechat": {"name": "公众号", "desc": "微信公众号文章"},
        "xiaohongshu": {"name": "小红书", "desc": "小红书笔记"},
        "zhihu": {"name": "知乎", "desc": "知乎文章/回答"},
        "baijiahao": {"name": "百家号", "desc": "百度百家号文章"},
        "weibo": {"name": "微博", "desc": "微博长文"},
        "sohu": {"name": "搜狐", "desc": "搜狐号文章"},
        "toutiao": {"name": "今日头条", "desc": "今日头条文章"},
        "qiehao": {"name": "企鹅号", "desc": "企鹅号（腾讯新闻）文章"},
        "jianshu": {"name": "简书", "desc": "简书文章"},
        "douban": {"name": "豆瓣", "desc": "豆瓣文章/日记"},
        "dayu": {"name": "大鱼号", "desc": "大鱼号（UC）文章"},
        "kr36": {"name": "36氪", "desc": "36氪文章"},
        "bilibili": {"name": "B站", "desc": "B站视频脚本/专栏"},
        "douyin": {"name": "抖音", "desc": "抖音短视频脚本"},
        "newsletter": {"name": "Newsletter", "desc": "邮件订阅"},
    }
    
    format_map = {"md": "Markdown", "html": "HTML", "docx": "Word"}
    format_class = {"md": "format-md", "html": "format-html", "docx": "format-docx"}
    
    # Build platform tables
    platform_tables = []
    total_files = 0
    for platform, files in platform_files.items():
        info = platform_info_map.get(platform, {"name": platform, "desc": platform})
        rows = []
        for fmt, fpath in files.items():
            if fmt == "images":
                continue
            fname = Path(fpath).name
            fmt_label = format_map.get(fmt, fmt.upper())
            fmt_cls = format_class.get(fmt, "format-md")
            total_files += 1
            if fmt == "docx":
                rows.append(f"""<tr>
                    <td>{fname}</td>
                    <td><span class="format-badge {fmt_cls}">{fmt_label}</span></td>
                    <td><a href="{fname}" class="btn btn-download" download>下载</a></td>
                </tr>""")
            else:
                rows.append(f"""<tr>
                    <td>{fname}</td>
                    <td><span class="format-badge {fmt_cls}">{fmt_label}</span></td>
                    <td>
                        <a href="{fname}" class="btn btn-preview" target="_blank">预览</a>
                        <a href="{fname}" class="btn btn-download" download>下载</a>
                    </td>
                </tr>""")
        
        table = f"""<h3>{info['name']}（{info['desc']}）</h3>
        <table>
            <thead>
                <tr>
                    <th>文件</th>
                    <th>格式</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>"""
        platform_tables.append(table)
    
    # Build image rows
    image_rows = []
    images_path = Path(images_dir) if images_dir else output / "images"
    if images_path.exists():
        for img in sorted(images_path.iterdir()):
            if img.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                is_cover = "cover" in img.name
                max_w = "80px" if not is_cover else "120px"
                max_h = "100px" if not is_cover else "60px"
                img_type = "封面" if is_cover else "配图"
                image_rows.append(f"""<tr>
                    <td><img src="images/{img.name}" alt="{img.name}" style="max-width: {max_w}; max-height: {max_h}; border-radius: 4px; cursor: pointer;" onclick="window.open('images/{img.name}', '_blank')"></td>
                    <td>{img.name}</td>
                    <td><span class="format-badge format-html">{img_type}</span></td>
                    <td>
                        <a href="images/{img.name}" class="btn btn-preview" target="_blank">查看原图</a>
                        <a href="images/{img.name}" class="btn btn-download" download>下载</a>
                    </td>
                </tr>""")
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件清单 - 可点击预览</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 40px 20px;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ font-size: 24px; margin-bottom: 8px; color: #1a1a1a; }}
        .subtitle {{ color: #666; margin-bottom: 24px; font-size: 14px; }}
        h2 {{ font-size: 18px; margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 2px solid #007bff; color: #1a1a1a; }}
        h3 {{ font-size: 16px; margin: 24px 0 12px; color: #333; }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 24px;
        }}
        th {{ background: #007bff; color: white; padding: 12px 16px; text-align: left; font-weight: 500; }}
        td {{ padding: 10px 16px; border-bottom: 1px solid #eee; }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover {{ background: #f8f9fa; }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .btn {{
            display: inline-block;
            padding: 6px 12px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 13px;
            transition: background 0.2s;
            margin-right: 4px;
        }}
        .btn:hover {{ background: #0056b3; text-decoration: none; }}
        .btn-download {{ background: #28a745; }}
        .btn-download:hover {{ background: #1e7e34; }}
        .btn-preview {{ background: #17a2b8; }}
        .btn-preview:hover {{ background: #138496; }}
        .format-badge {{
            display: inline-block;
            padding: 2px 8px;
            background: #e9ecef;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            color: #495057;
        }}
        .format-html {{ background: #cce5ff; color: #004085; }}
        .format-md {{ background: #d4edda; color: #155724; }}
        .format-docx {{ background: #fff3cd; color: #856404; }}
        .tip {{
            background: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 12px 16px;
            margin: 24px 0;
            border-radius: 0 8px 8px 0;
            font-size: 14px;
            color: #004085;
        }}
        .stats {{
            display: flex;
            gap: 24px;
            margin-top: 24px;
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .stat-item {{ text-align: center; flex: 1; }}
        .stat-number {{ font-size: 32px; font-weight: bold; color: #007bff; }}
        .stat-label {{ font-size: 14px; color: #666; margin-top: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📂 文件清单 - 可点击预览</h1>
        <p class="subtitle">输出目录: {output.name}/</p>

        <div class="tip">
            💡 提示：点击"预览"在浏览器中查看，点击"下载"保存到本地。图片需手动上传到各平台。
        </div>

        <h2>📄 快速导航</h2>
        <table>
            <thead>
                <tr>
                    <th>文件</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>README_文件说明.html</strong> — 文件使用说明与发布指引</td>
                    <td><a href="README_文件说明.html" class="btn btn-preview" target="_blank">打开</a></td>
                </tr>
                <tr>
                    <td><strong>图片清单.html</strong> — 所有配图预览与下载</td>
                    <td><a href="图片清单.html" class="btn btn-preview" target="_blank">打开</a></td>
                </tr>
            </tbody>
        </table>

        <h2>📱 各平台文件</h2>
        {''.join(platform_tables)}

        <h2>🖼️ 图片文件</h2>
        <table>
            <thead>
                <tr>
                    <th>缩略图</th>
                    <th>文件名</th>
                    <th>类型</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                {''.join(image_rows) if image_rows else '<tr><td colspan="4">暂无图片文件</td></tr>'}
            </tbody>
        </table>

        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{len(platform_files)}</div>
                <div class="stat-label">平台</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_files}</div>
                <div class="stat-label">文件</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(image_rows)}</div>
                <div class="stat-label">图片</div>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    preview_path = output / "文件清单_可点击预览.html"
    preview_path.write_text(html_content, encoding="utf-8")
    return str(preview_path)


def export_all_platforms(md_content: str, output_dir: str, theme_name: str = "professional-clean", images_dir: str = None):
    """Export content for all supported platforms.

    Args:
        md_content: Source Markdown content
        output_dir: Output directory path
        theme_name: Theme name for HTML conversion
        images_dir: Images directory path

    Returns:
        dict mapping platform -> exported file paths
    """
    results = {}
    for platform in SUPPORTED_PLATFORMS:
        results[platform] = export_platform(md_content, platform, output_dir, theme_name, images_dir)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Multi-platform file exporter")
    sub = parser.add_subparsers(dest="command", required=True)

    p_export = sub.add_parser("export", help="Export to platform-specific files")
    p_export.add_argument("input", help="Markdown file path")
    p_export.add_argument("--platform", required=True, help="Target platform or 'all'")
    p_export.add_argument("--output", required=True, help="Output directory")
    p_export.add_argument("--theme", default="professional-clean", help="Theme name for HTML platforms")
    p_export.add_argument("--images", help="Images directory to copy")

    args = parser.parse_args()

    md_content = Path(args.input).read_text(encoding="utf-8")
    style = _load_style()
    theme = args.theme or style.get("theme", "professional-clean")

    if args.platform == "all":
        results = export_all_platforms(md_content, args.output, theme, args.images)
        print(f"Exported {len(results)} platforms to {args.output}")
        for platform, files in results.items():
            print(f"  {platform}: {', '.join(files.values())}")
    else:
        if args.platform not in SUPPORTED_PLATFORMS:
            print(f"Error: unsupported platform '{args.platform}'", file=sys.stderr)
            print(f"Supported: {', '.join(SUPPORTED_PLATFORMS)}", file=sys.stderr)
            sys.exit(1)
        results = export_platform(md_content, args.platform, args.output, theme, args.images)
        print(f"Exported {args.platform} to {args.output}")
        for fmt, path in results.items():
            print(f"  {fmt}: {path}")
