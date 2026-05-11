#!/usr/bin/env python3
"""
Convert an article (Markdown) into platform-specific video scripts.

Supports:
  - bilibili: 3-8 minute video script with scene descriptions
  - douyin: 15-60 second short video script with hook and pacing
  - newsletter: HTML email with inline styles

Usage:
    python3 scripts/convert_to_video.py article.md --platform bilibili
    python3 scripts/convert_to_video.py article.md --platform douyin
    python3 scripts/convert_to_video.py article.md --platform newsletter
    python3 scripts/convert_to_video.py article.md --all
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime

import yaml

# --- Configuration ---

SPEECH_RATE_BILIBILI = 220  # chars per minute
SPEECH_RATE_DOUYIN = 250    # chars per minute

BILIBILI_HOOKS = [
    "你知道吗？最近有一个特别值得关注的事……",
    "先问个问题：你有没有想过……",
    "说实话，我之前对这个也很怀疑，直到我……",
    "今天聊一个我觉得很多人都会感兴趣的话题。",
]

DOUYIN_HOOKS = [
    "别划走！这个你一定要知道！",
    "90%的人都不知道的事……",
    "如果你也在做{topic}，这条视频一定要看完！",
    "我用这个方法，效率提升了300%！",
]

DOUYIN_CTAS = [
    "觉得有用的话，点个赞支持一下～",
    "关注我，每天一个实用技巧！",
    "你遇到过这个问题吗？评论区聊聊～",
    "收藏起来，以后一定用得上！",
]

BILIBILI_CTAS = [
    "如果这个视频对你有帮助，麻烦三连支持一下～",
    "你觉得呢？欢迎在弹幕和评论区聊聊你的看法。",
    "喜欢这类内容的话，记得点个关注，我们下期见。",
]


def extract_article_content(md_path):
    """Extract structured content from a Markdown article."""
    text = Path(md_path).read_text(encoding="utf-8")

    # Extract title
    title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Untitled"

    # Extract sections
    sections = re.split(r'^##\s+', text, flags=re.MULTILINE)
    parsed_sections = []

    for section in sections:
        lines = section.strip().split("\n")
        if not lines:
            continue
        heading = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        # Remove markdown formatting for speech
        body_clean = re.sub(r'[#*>\[\]()]', '', body)
        body_clean = re.sub(r'!\[.*?\]\(.*?\)', '[配图]', body_clean)
        body_clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', body_clean)

        if heading and body_clean:
            parsed_sections.append({
                "heading": heading,
                "body": body_clean,
                "char_count": len(body_clean),
            })

    return {
        "title": title,
        "sections": parsed_sections,
        "total_chars": sum(s["char_count"] for s in parsed_sections),
    }


def convert_to_bilibili_script(article: dict) -> dict:
    """Convert article to a Bilibili video script."""
    intro_hook = BILIBILI_HOOKS[hash(article["title"]) % len(BILIBILI_HOOKS)]
    cta = BILIBILI_CTAS[hash(article["title"]) % len(BILIBILI_CTAS)]

    total_speech_chars = 0
    scenes = []

    # Scene 0: Hook
    hook_len = len(intro_hook)
    scenes.append({
        "scene": 0,
        "type": "hook",
        "duration_sec": round(hook_len / (SPEECH_RATE_BILIBILI / 60)),
        "visual": "主播出镜或主题画面，标题文字出现",
        "speech": intro_hook,
        "notes": "前 5 秒要抓住注意力",
    })
    total_speech_chars += hook_len

    # Scene 1-N: Content sections
    for i, section in enumerate(article["sections"], 1):
        char_count = section["char_count"]
        duration_sec = round(char_count / (SPEECH_RATE_BILIBILI / 60))
        visual = _suggest_visual_for_section(section["heading"])

        scenes.append({
            "scene": i,
            "type": "content",
            "section": section["heading"],
            "duration_sec": duration_sec,
            "visual": visual,
            "speech": section["body"],
            "notes": f"预计时长 {duration_sec} 秒",
        })
        total_speech_chars += char_count

    # Scene N+1: CTA
    cta_len = len(cta)
    scenes.append({
        "scene": len(scenes) + 1,
        "type": "cta",
        "duration_sec": round(cta_len / (SPEECH_RATE_BILIBILI / 60)),
        "visual": "主播出镜，微笑引导互动",
        "speech": cta,
        "notes": "引导三连",
    })
    total_speech_chars += cta_len

    total_duration = sum(s["duration_sec"] for s in scenes)

    return {
        "platform": "bilibili",
        "title": article["title"],
        "estimated_duration_min": round(total_duration / 60, 1),
        "total_speech_chars": total_speech_chars,
        "cover_prompt": f"视频封面：{article['title']}，科技感背景，16:9，有冲击力",
        "scenes": scenes,
    }


def convert_to_douyin_script(article: dict) -> dict:
    """Convert article to a Douyin short video script."""
    # Pick 1-2 key points for short format
    if len(article["sections"]) > 2:
        key_sections = [article["sections"][0], article["sections"][1]]
    else:
        key_sections = article["sections"]

    topic = article["title"]
    hook = DOUYIN_HOOKS[hash(topic) % len(DOUYIN_HOOKS)].replace("{topic}", topic[:10])
    cta = DOUYIN_CTAS[hash(topic) % len(DOUYIN_CTAS)]

    # Trim content to fit 60 seconds
    max_chars = 60 * SPEECH_RATE_DOUYIN
    content = ""
    for s in key_sections:
        content += s["body"][:200] + "。"
        if len(content) > max_chars - len(hook) - len(cta):
            break

    actual_chars = len(hook) + len(content) + len(cta)
    duration_sec = round(actual_chars / (SPEECH_RATE_DOUYIN / 60))

    return {
        "platform": "douyin",
        "title": topic,
        "estimated_duration_sec": min(duration_sec, 60),
        "total_speech_chars": actual_chars,
        "cover_prompt": f"抖音封面：{topic[:20]}，视觉冲击力强，9:16",
        "script": {
            "hook": {
                "duration_sec": round(len(hook) / (SPEECH_RATE_DOUYIN / 60)),
                "text": hook,
                "visual": "前 3 秒抓人，主播表情惊讶/兴奋",
            },
            "content": {
                "duration_sec": round(len(content) / (SPEECH_RATE_DOUYIN / 60)),
                "text": content,
                "visual": "配合画面演示，字幕跟随",
            },
            "cta": {
                "duration_sec": round(len(cta) / (SPEECH_RATE_DOUYIN / 60)),
                "text": cta,
                "visual": "微笑引导，手势示意点赞",
            },
        },
    }


def convert_to_newsletter_html(article: dict, style: dict = None) -> str:
    """Convert article to an HTML email with inline styles."""
    subject_line = article["title"]
    preview_text = article["sections"][0]["body"][:100] if article["sections"] else ""

    html_parts = []
    html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject_line}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;">
<!-- Wrapper Table -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px 0;">
<tr>
<td align="center">
<!-- Content Table -->
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; max-width: 600px; width: 100%;">
<!-- Header -->
<tr>
<td style="background-color: #1a1a2e; color: #ffffff; padding: 40px 30px; text-align: center;">
<h1 style="margin: 0; font-size: 24px; line-height: 1.4;">{subject_line}</h1>
</td>
</tr>
<!-- Body -->
<tr>
<td style="padding: 30px; color: #333333; line-height: 1.8;">
""")

    for section in article["sections"]:
        html_parts.append(f'<h2 style="color: #1a1a2e; font-size: 20px; margin-top: 24px; margin-bottom: 12px;">{section["heading"]}</h2>')
        html_parts.append(f'<p style="margin: 0 0 16px 0; font-size: 16px;">{section["body"]}</p>')

    # Footer
    html_parts.append(f"""
</td>
</tr>
<!-- Footer -->
<tr>
<td style="background-color: #f8f8f8; padding: 20px 30px; text-align: center; color: #888888; font-size: 12px; border-top: 1px solid #eeeeee;">
<p style="margin: 0;">此邮件由 <strong>Writer</strong> 生成</p>
<p style="margin: 8px 0 0 0;">不想再收到此类邮件？<a href="#" style="color: #888888;">取消订阅</a></p>
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>""")

    html_content = "\n".join(html_parts)

    return {
        "html": html_content,
        "subject_line": subject_line,
        "preview_text": preview_text,
    }


def _suggest_visual_for_section(heading: str) -> str:
    """Suggest visual content for a section."""
    if "案例" in heading or "故事" in heading:
        return "案例画面：人物/产品照片 + 关键数据标注"
    elif "工具" in heading or "教程" in heading:
        return "屏幕录制：操作步骤演示"
    elif "对比" in heading:
        return "分屏对比：左右展示差异"
    elif "趋势" in heading or "数据" in heading:
        return "数据图表：柱状图/折线图/饼图"
    elif "避坑" in heading or "注意" in heading:
        return "警示画面：红色标记 + 错误示例"
    else:
        return "主播出镜讲解 + 关键文字叠加"


def format_script_bilibili(script: dict) -> str:
    """Format Bilibili script as Markdown."""
    lines = [f"# B站视频脚本：{script['title']}", ""]
    lines.append(f"预计时长：{script['estimated_duration_min']} 分钟")
    lines.append(f"封面提示词：{script['cover_prompt']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for scene in script["scenes"]:
        scene_type = {"hook": "🎬 开头钩子", "content": "📝 内容", "cta": "📢 互动引导"}.get(scene["type"], "📝")
        lines.append(f"## {scene_type}（{scene['duration_sec']} 秒）")
        lines.append("")
        lines.append(f"**画面**：{scene['visual']}")
        lines.append("")
        lines.append(f"**口播**：")
        lines.append(f"{scene['speech']}")
        if scene.get("notes"):
            lines.append(f"")
            lines.append(f"*备注：{scene['notes']}*")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def format_script_douyin(script: dict) -> str:
    """Format Douyin script as Markdown."""
    lines = [f"# 抖音视频脚本：{script['title']}", ""]
    lines.append(f"预计时长：{script['estimated_duration_sec']} 秒")
    lines.append(f"封面提示词：{script['cover_prompt']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for part_name, part in script["script"].items():
        part_type = {"hook": "🎬 开头钩子（前3秒）", "content": "📝 核心内容", "cta": "📢 互动引导"}.get(part_name, "📝")
        lines.append(f"## {part_type}（{part['duration_sec']} 秒）")
        lines.append("")
        lines.append(f"**画面**：{part['visual']}")
        lines.append("")
        lines.append(f"**口播**：")
        lines.append(f"{part['text']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Convert article to video scripts")
    parser.add_argument("input", help="Markdown article file")
    parser.add_argument("--platform", default="", help="Target platform (bilibili/douyin/newsletter)")
    parser.add_argument("--all", action="store_true", help="Generate for all platforms")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()

    if not args.platform and not args.all:
        print("Error: specify --platform or --all", file=sys.stderr)
        sys.exit(1)

    article = extract_article_content(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    platforms = ["bilibili", "douyin", "newsletter"] if args.all else [args.platform]

    for platform in platforms:
        if platform == "bilibili":
            script = convert_to_bilibili_script(article)
            formatted = format_script_bilibili(script)
            out_path = output_dir / f"bilibili_{Path(args.input).stem}.md"
            out_path.write_text(formatted, encoding="utf-8")
            print(f"Generated: {out_path}（{script['estimated_duration_min']} 分钟）")

        elif platform == "douyin":
            script = convert_to_douyin_script(article)
            formatted = format_script_douyin(script)
            out_path = output_dir / f"douyin_{Path(args.input).stem}.md"
            out_path.write_text(formatted, encoding="utf-8")
            print(f"Generated: {out_path}（{script['estimated_duration_sec']} 秒）")

        elif platform == "newsletter":
            result = convert_to_newsletter_html(article)
            out_html = output_dir / f"newsletter_{Path(args.input).stem}.html"
            out_html.write_text(result["html"], encoding="utf-8")
            print(f"Generated: {out_html}")
            print(f"  Subject: {result['subject_line']}")
            print(f"  Preview: {result['preview_text'][:50]}...")


if __name__ == "__main__":
    main()
