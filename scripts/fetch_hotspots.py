#!/usr/bin/env python3
"""
Fetch trending topics from multiple Chinese platforms.

Sources (all attempted in parallel, results merged and deduplicated):
  1. Weibo hot search (weibo.com/ajax/side/hotSearch)
  2. Toutiao hot board (toutiao.com/hot-event/hot-board)
  3. Baidu hot search (top.baidu.com/api/board)
  4. Douban hot topics (douban.com/group/explore)
  5. 36Kr hot articles (36kr.com/hot-list/catalog)
  6. Zhihu hot list (zhihu.com/hot)

Usage:
    python3 fetch_hotspots.py --limit 20
    python3 fetch_hotspots.py --limit 30 --sources weibo,baidu,36kr
    python3 fetch_hotspots.py --category tech
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta

import requests

TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


def fetch_weibo() -> list[dict]:
    """Fetch Weibo hot search."""
    try:
        resp = requests.get(
            "https://weibo.com/ajax/side/hotSearch",
            headers={**HEADERS, "Referer": "https://weibo.com/"},
            timeout=TIMEOUT,
        )
        data = resp.json()
        items = []
        for entry in data.get("data", {}).get("realtime", []):
            note = entry.get("note", "")
            if not note:
                continue
            items.append({
                "title": note,
                "source": "微博",
                "hot": entry.get("num", 0),
                "url": f"https://s.weibo.com/weibo?q=%23{note}%23",
                "description": entry.get("label_name", ""),
                "category": _classify_topic(note),
            })
        return items
    except Exception as e:
        print(f"[warn] weibo failed: {e}", file=sys.stderr)
        return []


def fetch_toutiao() -> list[dict]:
    """Fetch Toutiao hot board."""
    try:
        resp = requests.get(
            "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        data = resp.json()
        items = []
        for entry in data.get("data", []):
            title = entry.get("Title", "")
            if not title:
                continue
            items.append({
                "title": title,
                "source": "今日头条",
                "hot": int(entry.get("HotValue", 0) or 0),
                "url": entry.get("Url", ""),
                "description": "",
                "category": _classify_topic(title),
            })
        return items
    except Exception as e:
        print(f"[warn] toutiao failed: {e}", file=sys.stderr)
        return []


def fetch_baidu() -> list[dict]:
    """Fetch Baidu hot search."""
    try:
        resp = requests.get(
            "https://top.baidu.com/api/board?platform=wise&tab=realtime",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        data = resp.json()
        items = []
        for card in data.get("data", {}).get("cards", []):
            top_content = card.get("content", [])
            if not top_content:
                continue
            entries = top_content[0].get("content", []) if isinstance(top_content[0], dict) else top_content
            for entry in entries:
                word = entry.get("word", "")
                if not word:
                    continue
                items.append({
                    "title": word,
                    "source": "百度",
                    "hot": int(entry.get("hotScore", 0) or 0),
                    "url": entry.get("url", ""),
                    "description": "",
                    "category": _classify_topic(word),
                })
        return items
    except Exception as e:
        print(f"[warn] baidu failed: {e}", file=sys.stderr)
        return []


def fetch_douban() -> list[dict]:
    """Fetch Douban hot topics."""
    try:
        resp = requests.get(
            "https://frodo.douban.com/api/v2/topic/selected_items?topic_id=100",
            headers={**HEADERS, "Referer": "https://m.douban.com/"},
            timeout=TIMEOUT,
        )
        data = resp.json()
        items = []
        for entry in data.get("items", []):
            title = entry.get("title", "") or entry.get("text", "")
            if not title:
                continue
            items.append({
                "title": title,
                "source": "豆瓣",
                "hot": entry.get("rating", {}).get("value", 0),
                "url": entry.get("link", ""),
                "description": entry.get("abstract", ""),
                "category": _classify_topic(title),
            })
        return items
    except Exception as e:
        print(f"[warn] douban failed: {e}", file=sys.stderr)
        return []


def fetch_36kr() -> list[dict]:
    """Fetch 36Kr hot articles."""
    try:
        resp = requests.get(
            "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot",
            headers={**HEADERS, "Content-Type": "application/json", "Referer": "https://36kr.com/"},
            timeout=TIMEOUT,
            json={"partner_id": "wap", "param": {"siteId": 1}},
        )
        data = resp.json()
        items = []
        for entry in data.get("data", {}).get("hotRankList", []):
            title = entry.get("templateMaterial", {}).get("widgetTitle", "")
            if not title:
                continue
            items.append({
                "title": title,
                "source": "36氪",
                "hot": entry.get("statFavorite", 0),
                "url": f"https://36kr.com/p/{entry.get('itemId', '')}",
                "description": entry.get("templateMaterial", {}).get("widgetSubtitle", ""),
                "category": "科技" if not _classify_topic(title) else _classify_topic(title),
            })
        return items
    except Exception as e:
        print(f"[warn] 36kr failed: {e}", file=sys.stderr)
        return []


def fetch_zhihu() -> list[dict]:
    """Fetch Zhihu hot list."""
    try:
        resp = requests.get(
            "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20",
            headers={**HEADERS, "Referer": "https://www.zhihu.com/hot"},
            timeout=TIMEOUT,
        )
        data = resp.json()
        items = []
        for entry in data.get("data", []):
            target = entry.get("target", {})
            title = target.get("title", "")
            if not title:
                continue
            items.append({
                "title": title,
                "source": "知乎",
                "hot": entry.get("detail_text", "0").replace(" 热度", ""),
                "url": target.get("url", "").replace("api", "www"),
                "description": target.get("excerpt", ""),
                "category": _classify_topic(title),
            })
        return items
    except Exception as e:
        print(f"[warn] zhihu failed: {e}", file=sys.stderr)
        return []


def _classify_topic(title: str) -> str:
    """Classify topic into category based on keywords."""
    tech_words = ["AI", "人工智能", "大模型", "算法", "芯片", "科技", "互联网", "App", "软件", "代码", "编程", "SaaS", "GPT", "Claude", "OpenAI", "字节", "腾讯", "阿里", "百度", "华为", "小米"]
    business_words = ["融资", "上市", "IPO", "投资", "估值", "营收", "财报", "并购", "创业", "CEO", "公司", "企业", "商业"]
    society_words = ["政策", "法规", "教育", "医疗", "就业", "房价", "人口", "社会"]
    entertainment_words = ["电影", "音乐", "明星", "综艺", "电视剧", "游戏", "动漫"]

    for word in tech_words:
        if word.lower() in title.lower():
            return "科技"
    for word in business_words:
        if word in title:
            return "商业"
    for word in society_words:
        if word in title:
            return "社会"
    for word in entertainment_words:
        if word in title:
            return "娱乐"
    return "综合"


def deduplicate_smart(items: list[dict]) -> list[dict]:
    """Remove duplicates using fuzzy matching.

    Two titles are considered duplicates if:
    1. Exact match after normalization
    2. One contains the other (length difference > 5 chars)
    3. Jaccard similarity of character sets > 0.7
    """
    def normalize(text):
        return re.sub(r'[^\u4e00-\u9fff\w]', '', text.lower())

    def jaccard_sim(a, b):
        set_a = set(a)
        set_b = set(b)
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0

    def is_duplicate(t1, t2):
        n1, n2 = normalize(t1), normalize(t2)
        if n1 == n2:
            return True
        if n1 in n2 or n2 in n1:
            return True
        if jaccard_sim(n1, n2) > 0.7:
            return True
        return False

    seen = []
    result = []
    for item in items:
        title = item["title"].strip()
        is_dup = False
        for seen_item in seen:
            if is_duplicate(title, seen_item["title"]):
                # Keep the one with higher hot score
                if item.get("hot_normalized", 0) > seen_item.get("hot_normalized", 0):
                    seen.remove(seen_item)
                    seen.append(item)
                    # Replace in result
                    result = [r for r in result if r["title"] != seen_item["title"]]
                    result.append(item)
                is_dup = True
                break
        if not is_dup:
            seen.append(item)
            result.append(item)
    return result


def main():
    parser = argparse.ArgumentParser(description="Fetch trending topics from multiple sources")
    parser.add_argument("--limit", type=int, default=20, help="Max items to return")
    parser.add_argument("--sources", type=str, default="", help="Comma-separated source names to use")
    parser.add_argument("--category", type=str, default="", help="Filter by category (科技/商业/社会/娱乐)")
    args = parser.parse_args()

    all_fetchers = {
        "weibo": fetch_weibo,
        "toutiao": fetch_toutiao,
        "baidu": fetch_baidu,
        "douban": fetch_douban,
        "36kr": fetch_36kr,
        "zhihu": fetch_zhihu,
    }

    if args.sources:
        selected_sources = [s.strip() for s in args.sources.split(",")]
        fetchers = {k: v for k, v in all_fetchers.items() if k in selected_sources}
    else:
        fetchers = all_fetchers

    all_items = []
    sources_ok = []
    sources_fail = []

    for name, fetcher in fetchers.items():
        items = fetcher()
        if items:
            sources_ok.append(name)
            all_items.extend(items)
        else:
            sources_fail.append(name)

    # Normalize hot values within each source
    by_source = {}
    for item in all_items:
        by_source.setdefault(item["source"], []).append(item)

    for source, items in by_source.items():
        items.sort(key=lambda x: int(x.get("hot", 0) or 0), reverse=True)
        n = len(items)
        for rank, item in enumerate(items):
            item["hot_normalized"] = round(100 * (n - rank) / n, 1) if n > 0 else 0

    # Merge and deduplicate
    all_items.sort(key=lambda x: x.get("hot_normalized", 0), reverse=True)
    all_items = deduplicate_smart(all_items)

    # Filter by category if specified
    if args.category:
        all_items = [item for item in all_items if item.get("category") == args.category]

    all_items = all_items[:args.limit]

    tz = timezone(timedelta(hours=8))
    output = {
        "timestamp": datetime.now(tz).isoformat(),
        "sources": sources_ok,
        "sources_failed": sources_fail,
        "count": len(all_items),
        "items": all_items,
    }

    if not all_items:
        output["error"] = "All sources failed. SKILL.md should fall back to WebSearch."

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
