#!/usr/bin/env python3
"""
Per-platform image generation for Writer.

Generates platform-specific images based on article content and platform requirements.
Each platform gets different images with unique prompts, styles, and compositions.

Usage as module:
    from platform_images import generate_platform_images
    images = generate_platform_images(platform, article, output_dir)
"""

from pathlib import Path
import sys
import re

from image_gen import generate_image, _load_config

PLATFORM_IMAGE_CONFIGS = {
    "wechat": {
        "cover": {"size": "cover_wechat", "desc": "微信公众号封面图"},
        "images": [
            {"size": "article", "count": 3, "desc": "正文配图"},
        ],
    },
    "xiaohongshu": {
        "cover": {"size": "cover_xiaohongshu", "desc": "小红书封面图（3:4竖版）"},
        "images": [
            {"size": "cover_xiaohongshu", "count": 5, "desc": "笔记配图"},
        ],
    },
    "zhihu": {
        "cover": {"size": "16:9", "desc": "知乎封面图"},
        "images": [
            {"size": "article", "count": 2, "desc": "正文配图"},
        ],
    },
    "baijiahao": {
        "cover": {"size": "16:9", "desc": "百家号封面图"},
        "images": [
            {"size": "article", "count": 2, "desc": "正文配图"},
        ],
    },
    "weibo": {
        "cover": {"size": "2048x2048", "desc": "微博配图（正方形）"},
        "images": [
            {"size": "1:1", "count": 3, "desc": "微博配图"},
        ],
    },
    "sohu": {
        "cover": {"size": "16:9", "desc": "搜狐号封面图"},
        "images": [
            {"size": "article", "count": 2, "desc": "正文配图"},
        ],
    },
    "toutiao": {
        "cover": {"size": "16:9", "desc": "今日头条三图封面"},
        "images": [
            {"size": "article", "count": 3, "desc": "正文配图"},
        ],
    },
    "qiehao": {
        "cover": {"size": "16:9", "desc": "企鹅号封面图"},
        "images": [
            {"size": "article", "count": 2, "desc": "正文配图"},
        ],
    },
    "jianshu": {
        "cover": {"size": "16:9", "desc": "简书封面图"},
        "images": [
            {"size": "article", "count": 2, "desc": "正文配图"},
        ],
    },
    "douban": {
        "cover": {"size": "16:9", "desc": "豆瓣封面图"},
        "images": [
            {"size": "article", "count": 1, "desc": "正文配图"},
        ],
    },
    "dayu": {
        "cover": {"size": "16:9", "desc": "大鱼号封面图"},
        "images": [
            {"size": "article", "count": 2, "desc": "正文配图"},
        ],
    },
    "kr36": {
        "cover": {"size": "16:9", "desc": "36氪封面图"},
        "images": [
            {"size": "article", "count": 2, "desc": "正文配图"},
        ],
    },
    "bilibili": {
        "cover": {"size": "16:9", "desc": "B站封面图（信息量大、标题突出）"},
        "images": [
            {"size": "article", "count": 2, "desc": "专栏配图"},
        ],
    },
    "douyin": {
        "cover": {"size": "1792x2304", "desc": "抖音竖版封面（9:16）"},
        "images": [
            {"size": "vertical", "count": 1, "desc": "竖版配图"},
        ],
    },
    "newsletter": {
        "cover": {"size": "16:9", "desc": "Newsletter 题图"},
        "images": [],
    },
}


PLATFORM_IMAGE_STYLES = {
    "wechat": "商务专业,蓝色调,扁平化设计,科技感",
    "xiaohongshu": "时尚感强,渐变色背景,醒目文字,小红书风格",
    "zhihu": "知识分享风格,专业感,蓝色调,数据可视化",
    "baijiahao": "新闻资讯风格,客观中立,正式严肃",
    "weibo": "视觉冲击力强,社交媒体传播,热点新闻风格",
    "sohu": "新闻报道风格,信息量大,媒体感",
    "toutiao": "接地气,吸引点击,生活化场景",
    "qiehao": "科技新闻风格,简洁大气,现代感",
    "jianshu": "文艺清新,简约,有温度",
    "douban": "文艺感强,有深度,电影感",
    "dayu": "信息量大,UC风格,吸引眼球",
    "kr36": "科技创投风格,现代感,硅谷风",
    "bilibili": "信息量大,有冲击力,标题文字突出,二次元感",
    "douyin": "视觉冲击力强,竖版构图,短视频封面风格",
    "newsletter": "专业商务,简洁,国际化",
}


IMAGE_ANGLE_POOL = {
    "wechat": ["数据可视化图表", "商务场景", "办公环境", "团队讨论"],
    "xiaohongshu": ["信息卡片", "对比图表", "生活场景", "产品特写", "人物肖像"],
    "zhihu": ["数据分析图", "技术架构图", "对比表格", "流程图", "趋势图"],
    "baijiahao": ["新闻现场", "官方照片风格", "权威机构", "数据报告"],
    "weibo": ["热点新闻图", "话题讨论", "用户评论", "事件时间线"],
    "sohu": ["媒体报道", "专家访谈", "行业分析", "市场数据"],
    "toutiao": ["生活场景", "街头采访", "数据图表", "热点事件"],
    "qiehao": ["科技产品", "数据大屏", "会议现场", "专家观点"],
    "jianshu": ["书房场景", "手写笔记", "咖啡桌", "阅读氛围"],
    "douban": ["电影海报风格", "书封设计", "艺术摄影", "城市街景"],
    "dayu": ["震撼大图", "数据对比", "人物特写", "场景还原"],
    "kr36": ["创投场景", "数据分析", "产品演示", "行业趋势"],
    "bilibili": ["弹幕风格", "对比截图", "数据图表", "场景还原"],
    "douyin": ["短视频封面", "数字大字报", "对比图", "事件回顾"],
    "newsletter": ["商务会议", "数据报告", "全球视野", "趋势分析"],
}


def _extract_title(article: str) -> str:
    """Extract H1 title from article."""
    for line in article.split("\n")[:10]:
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _extract_keywords(article: str, count: int = 5) -> list:
    """Extract key terms from article for image prompts."""
    text = article.replace("#", "").replace("*", "").replace("\n", " ")
    words = re.findall(r'[\u4e00-\u9fff]{2,8}', text)
    freq = {}
    for w in words:
        if len(w) >= 2:
            freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_words[:count]]


def _build_image_prompt(
    platform: str,
    article: str,
    image_type: str,
    index: int,
    seed: int = 0,
) -> str:
    """
    Build an image generation prompt based on platform, article, and image type.
    Each platform gets a different prompt with unique angle, style, and composition.
    """
    title = _extract_title(article)
    keywords = _extract_keywords(article)
    style = PLATFORM_IMAGE_STYLES.get(platform, "专业")
    angles = IMAGE_ANGLE_POOL.get(platform, ["数据图表"])

    if image_type == "cover":
        angle = angles[seed % len(angles)]
        return f"{title}，{angle}，{style}，无文字，高质量，精细"

    angle = angles[(index + seed) % len(angles)]
    kw = keywords[index % len(keywords)] if keywords else ""
    return f"{title}相关，{kw}主题，{angle}，{style}，信息可视化，高质量"


def generate_platform_images(
    platform: str,
    article: str,
    output_dir: str,
    config: dict = None,
    seed: int = 0,
) -> dict:
    """
    Generate platform-specific images.

    Args:
        platform: Platform key
        article: Article markdown content
        output_dir: Directory to save images
        config: Optional config
        seed: Random seed for prompt variation (different seed = different images)

    Returns:
        Dict of {image_key: image_path}
    """
    if config is None:
        config = _load_config()

    img_cfg = PLATFORM_IMAGE_CONFIGS.get(platform, {})
    if not img_cfg:
        return {}

    out = Path(output_dir) / platform
    out.mkdir(parents=True, exist_ok=True)

    images = {}

    cover_cfg = img_cfg.get("cover")
    if cover_cfg:
        prompt = _build_image_prompt(platform, article, "cover", 0, seed=seed)
        cover_name = f"cover_{platform}.png"
        try:
            cover_path = generate_image(prompt, str(out / cover_name), size=cover_cfg["size"], config=config)
            images["cover"] = cover_path
            print(f"    ✅ 封面: {cover_name}")
        except Exception as e:
            print(f"    ❌ 封面生成失败: {e}")

    for img_spec in img_cfg.get("images", []):
        size = img_spec["size"]
        count = img_spec["count"]
        desc = img_spec["desc"]

        for i in range(count):
            prompt = _build_image_prompt(platform, article, "article", i, seed=seed + i)
            img_name = f"img_{platform}_{i+1}.png"
            try:
                img_path = generate_image(prompt, str(out / img_name), size=size, config=config)
                images[f"img_{i+1}"] = img_path
                print(f"    ✅ 配图{i+1}: {img_name}")
            except Exception as e:
                print(f"    ❌ 配图{i+1}生成失败: {e}")

    return images
