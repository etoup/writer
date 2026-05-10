#!/usr/bin/env python3
"""
SEO keyword research tool — multi-platform.

Queries real search data to evaluate keyword popularity:
  1. Baidu search suggestions (autocomplete volume proxy)
  2. Baidu related searches
  3. WeChat sogou index (search volume proxy)
  4. Platform-specific tag recommendations (Xiaohongshu, Zhihu, Weibo)

Usage:
    python3 seo_keywords.py "AI大模型"
    python3 seo_keywords.py "AI大模型" "科技股" "创业"
    python3 seo_keywords.py --json "AI大模型"
    python3 seo_keywords.py --platform xiaohongshu "AI工具"

Output: keyword popularity score, related keywords, trending signals, platform tags.
"""

import argparse
import json
import re
import sys
import urllib.parse

import requests

TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36",
}

PLATFORM_TAG_MAP = {
    "xiaohongshu": {
        "prefix": "",
        "suffix": "",
        "separator": " ",
        "max_tags": 10,
        "style": "emoji_prefix",
    },
    "zhihu": {
        "prefix": "",
        "suffix": "",
        "separator": "、",
        "max_tags": 5,
        "style": "plain",
    },
    "weibo": {
        "prefix": "#",
        "suffix": "#",
        "separator": " ",
        "max_tags": 3,
        "style": "hashtag",
    },
    "wechat": {
        "prefix": "",
        "suffix": "",
        "separator": ",",
        "max_tags": 5,
        "style": "comma_separated",
    },
}

EMOJI_CATEGORIES = {
    "科技": "💻", "AI": "🤖", "工具": "🛠️", "教程": "📝",
    "测评": "📊", "推荐": "⭐", "避坑": "⚠️", "经验": "💡",
    "赚钱": "💰", "副业": "💼", "效率": "⚡", "学习": "📚",
    "生活": "🌈", "情感": "❤️", "职场": "🏢", "创业": "🚀",
}


def baidu_suggestions(keyword: str) -> list[str]:
    """Get Baidu search autocomplete suggestions."""
    try:
        resp = requests.get(
            "https://suggestion.baidu.com/su",
            params={"wd": keyword, "action": "opensearch", "ie": "utf-8"},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        data = resp.json()
        if isinstance(data, list) and len(data) >= 2:
            return data[1]
        return []
    except Exception as e:
        print(f"[warn] baidu suggestions failed: {e}", file=sys.stderr)
        return []


def so360_suggestions(keyword: str) -> list[str]:
    """Get 360 search suggestions."""
    try:
        resp = requests.get(
            "https://sug.so.360.cn/suggest",
            params={"word": keyword, "encodein": "utf-8", "encodeout": "utf-8", "format": "json"},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        data = resp.json()
        return [item.get("word", "") for item in data.get("result", []) if item.get("word")]
    except Exception as e:
        print(f"[warn] 360 suggestions failed: {e}", file=sys.stderr)
        return []


def generate_platform_tags(keyword: str, related: list[str], platform: str) -> list[str]:
    """Generate platform-specific tags/hashtags."""
    config = PLATFORM_TAG_MAP.get(platform, PLATFORM_TAG_MAP["wechat"])

    # Select top keywords for tags
    all_keywords = [keyword] + related
    tags = []

    for kw in all_keywords[:config["max_tags"]]:
        tag = kw
        if config["style"] == "emoji_prefix":
            emoji = _get_emoji_for_keyword(kw)
            tag = f"{emoji}{kw}" if emoji else kw
        elif config["style"] == "hashtag":
            tag = f"{config['prefix']}{kw}{config['suffix']}"

        tags.append(tag)

    return tags


def _get_emoji_for_keyword(kw: str) -> str:
    """Get relevant emoji for a keyword."""
    for key, emoji in EMOJI_CATEGORIES.items():
        if key.lower() in kw.lower():
            return emoji
    return ""


def analyze_keyword(keyword: str, platform: str = "wechat") -> dict:
    """Analyze a keyword's SEO potential across platforms."""
    baidu_suggs = baidu_suggestions(keyword)
    so360_suggs = so360_suggestions(keyword)

    baidu_score = min(len(baidu_suggs), 10)
    so360_score = min(len(so360_suggs), 10)
    combined_score = round((baidu_score + so360_score) / 2, 1)

    all_related = list(dict.fromkeys(baidu_suggs + so360_suggs))

    # Platform-specific tags
    tags = generate_platform_tags(keyword, all_related, platform)

    # Title suggestions based on platform
    title_suggestions = _generate_title_suggestions(keyword, all_related, platform)

    return {
        "keyword": keyword,
        "seo_score": combined_score,
        "baidu_score": baidu_score,
        "so360_score": so360_score,
        "baidu_suggestions": baidu_suggs[:5],
        "so360_suggestions": so360_suggs[:5],
        "related_keywords": all_related[:10],
        "platform_tags": tags,
        "title_suggestions": title_suggestions,
    }


def _generate_title_suggestions(keyword: str, related: list[str], platform: str) -> list[dict]:
    """Generate title suggestions based on platform characteristics."""
    titles = []

    if platform == "xiaohongshu":
        titles = [
            {"title": f"2026年了，{keyword}到底怎么用？一篇讲清楚", "style": "教程型"},
            {"title": f"别再乱用{keyword}了！这3个技巧太实用了", "style": "避坑型"},
            {"title": f"我用{keyword}，效率提升了300%", "style": "数据型"},
        ]
    elif platform == "zhihu":
        titles = [
            {"title": f"如何评价{keyword}的最新发展？有哪些值得关注的趋势？", "style": "分析型"},
            {"title": f"{keyword}真的能替代传统方案吗？深度对比分析", "style": "对比型"},
            {"title": f"一文读懂{keyword}：从原理到实践", "style": "科普型"},
        ]
    elif platform == "weibo":
        titles = [
            {"title": f"#{keyword}# 冲上热搜！这个新功能太炸了", "style": "热点型"},
            {"title": f"关于{keyword}，说几个你可能不知道的真相", "style": "揭秘型"},
        ]
    else:
        titles = [
            {"title": f"{keyword}全解析：你需要知道的一切", "style": "综合型"},
            {"title": f"2026年{keyword}趋势展望", "style": "趋势型"},
            {"title": f"为什么{keyword}正在改变我们的工作方式？", "style": "观点型"},
        ]

    return titles


def main():
    parser = argparse.ArgumentParser(description="SEO keyword analysis (multi-platform)")
    parser.add_argument("keywords", nargs="+", help="Keywords to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--platform", default="wechat",
                       help="Target platform (wechat/xiaohongshu/zhihu/weibo)")
    args = parser.parse_args()

    results = []
    for kw in args.keywords:
        result = analyze_keyword(kw, args.platform)
        results.append(result)

    if args.json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    else:
        platform_names = {
            "wechat": "公众号", "xiaohongshu": "小红书",
            "zhihu": "知乎", "weibo": "微博",
        }
        pname = platform_names.get(args.platform, args.platform)

        for r in results:
            print(f"\n关键词: {r['keyword']}")
            print(f"  综合 SEO 评分: {r['seo_score']}/10（百度 {r['baidu_score']} + 360 {r['so360_score']}）")
            if r["related_keywords"]:
                print(f"  相关关键词: {', '.join(r['related_keywords'][:5])}")
            if r["platform_tags"]:
                tags_str = " ".join(r["platform_tags"]) if args.platform == "xiaohongshu" else ", ".join(r["platform_tags"])
                print(f"  {pname}推荐标签: {tags_str}")
            if r["title_suggestions"]:
                print(f"  标题建议:")
                for t in r["title_suggestions"]:
                    print(f"    - [{t['style']}] {t['title']}")


if __name__ == "__main__":
    main()
