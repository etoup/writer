#!/usr/bin/env python3
"""
Per-platform article writer for Writer.

Generates unique articles for each platform based on the same topic,
following each platform's specific requirements (word count, style, structure, etc.).

Supports two modes:
  1. LLM API mode: Uses configured text providers to generate articles
  2. Dialog mode: Outputs platform requirements for AI assistant to write in conversation

Key features:
  - Deduplication engine: reads history.yaml to avoid duplicate angles/frameworks
  - Platform-specific prompts with different frameworks per platform
  - Random seed variation for additional diversity

Usage as module:
    from platform_writer import write_for_platforms
    results = write_for_platforms(topic, platforms=["wechat", "xiaohongshu"])
"""

from pathlib import Path
import yaml
import re
import random
import hashlib

from text_gen import generate_text, _load_config

CONFIG_PATHS = [
    Path.cwd() / "config.yaml",
    Path(__file__).parent.parent / "config.yaml",
    Path(__file__).parent / "config.yaml",
    Path.home() / ".config" / "writer" / "config.yaml",
]

PLATFORM_SPECS = {}

PLATFORMS_DIR = Path(__file__).parent.parent / "platforms"
if PLATFORMS_DIR.exists():
    for spec_file in sorted(PLATFORMS_DIR.glob("*.md")):
        platform_key = spec_file.stem
        with open(spec_file, "r", encoding="utf-8") as f:
            PLATFORM_SPECS[platform_key] = f.read()

STYLE_PATHS = [
    Path.cwd() / "style.yaml",
    Path(__file__).parent.parent / "style.yaml",
    Path.home() / ".config" / "writer" / "style.yaml",
]


def _load_style() -> dict:
    for p in STYLE_PATHS:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


HISTORY_PATHS = [
    Path.cwd() / "history.yaml",
    Path(__file__).parent.parent / "history.yaml",
    Path.home() / ".config" / "writer" / "history.yaml",
]


def _load_history() -> list:
    """Load history.yaml to check for duplicate articles."""
    for p in HISTORY_PATHS:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
    return []


def _save_history(entry: dict):
    """Append an entry to history.yaml."""
    history = _load_history()
    history.append(entry)
    for p in HISTORY_PATHS:
        if p.parent.exists():
            try:
                with open(p, "w", encoding="utf-8") as f:
                    yaml.dump(history, f, allow_unicode=True, default_flow_style=False)
                return
            except Exception:
                pass


def _get_used_angles(topic_keywords: list, platform: str, history: list) -> list:
    """Extract already-used titles/frameworks for deduplication."""
    used = []
    for entry in history:
        kw = entry.get("topic_keywords", [])
        platforms = entry.get("platforms", [])
        if any(k in topic_keywords for k in kw) and platform in platforms:
            title = entry.get("title", "")
            framework = entry.get("framework", "")
            closing = entry.get("closing_type", "")
            dims = entry.get("dimensions", [])
            used.append({
                "title": title,
                "framework": framework,
                "closing": closing,
                "dimensions": dims,
            })
    return used


def _build_dedup_instruction(used: list) -> str:
    """Build deduplication instruction string."""
    if not used:
        return ""
    
    lines = ["\n⚠️ 去重要求（必须遵守）："]
    titles = set()
    frameworks = set()
    closings = set()
    dims = set()
    
    for u in used:
        if u.get("title"):
            titles.add(u["title"][:40])
        if u.get("framework"):
            frameworks.add(u["framework"])
        if u.get("closing"):
            closings.add(u["closing"])
        for d in u.get("dimensions", []):
            dims.add(str(d))
    
    if titles:
        lines.append(f"- 标题不能与已有文章重复，避免使用：{'、'.join(list(titles)[:3])}")
    if frameworks:
        lines.append(f"- 避免使用相同框架：{'、'.join(list(frameworks)[:3])}")
    if closings:
        lines.append(f"- 避免使用相同收尾方式：{'、'.join(list(closings)[:3])}")
    
    return "\n".join(lines)


FRAMEWORKS_PATH = Path(__file__).parent.parent / "references" / "frameworks.md"
GUIDELINES_PATH = Path(__file__).parent.parent / "references" / "writing-guidelines.md"
GUIDE_PATH = Path(__file__).parent.parent / "references" / "writing-guide.md"


def _load_reference(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


FRAMEWORK_PROMPTS = {
    "对比": "使用对比框架：A vs B，帮助读者看清差异。从对立维度切入，用对比表格和对比案例支撑观点",
    "痛点": "使用痛点框架：共鸣 → 放大 → 破局。从读者最痛的点切入，逐步放大问题的严重性，最后给出解决方案",
    "清单": "使用清单框架：条目式，清晰实用。每条包含核心观点+具体案例，让读者可以直接使用",
    "故事": "使用故事框架：背景 → 转折 → 高潮 → 结局。用叙事吸引读者，在关键时刻给出洞察",
    "观点": "使用纯观点框架：亮明立场 → 论证 → 总结。开篇直接亮出核心观点，然后用2-3个论据支撑",
    "热点解读": "使用热点解读框架：事件回顾 → 深层分析 → 影响预判 → 应对建议。先帮读者理解事件，再给出独家洞察",
    "复盘": "使用复盘框架：时间线 → 关键节点 → 转折点 → 启示。梳理事件发展脉络，提取可复用的经验",
    "测评": "使用测评框架：维度定义 → 逐项对比 → 优缺点 → 推荐建议。客观公正，数据说话",
    "纯观点": "使用纯观点框架：立场 → 论证 → 总结。开篇直接亮出核心观点，然后用论据支撑",
}

PLATFORM_NAME_MAP = {
    "wechat": "微信公众号",
    "xiaohongshu": "小红书",
    "zhihu": "知乎",
    "baijiahao": "百度百家号",
    "weibo": "微博",
    "sohu": "搜狐号",
    "toutiao": "今日头条",
    "qiehao": "企鹅号",
    "jianshu": "简书",
    "douban": "豆瓣",
    "dayu": "大鱼号",
    "kr36": "36氪",
    "bilibili": "哔哩哔哩（B站）专栏",
    "douyin": "抖音图文",
    "newsletter": "Newsletter 邮件",
}


def write_for_platform(
    topic: str,
    platform: str,
    framework: str = "对比",
    seed: int = None,
    config: dict = None,
    history: list = None,
) -> str:
    """
    Write a unique article for a specific platform.

    Args:
        topic: The topic/title of the article
        platform: Platform key (wechat, xiaohongshu, zhihu, etc.)
        framework: Writing framework (对比, 痛点, 清单, 故事, 观点)
        seed: Random seed for variation (auto-incremented if None)
        config: Optional config dict
        history: History entries for deduplication (auto-loaded if None)

    Returns:
        The generated article in Markdown format.
    """
    if config is None:
        config = _load_config()
    if history is None:
        history = _load_history()

    style_cfg = _load_style()
    spec = PLATFORM_SPECS.get(platform, "")

    # Parse platform spec
    word_count = "1200-2000"
    style_desc = "专业干货"
    structure = "开头 → 正文 → 结尾"
    tone = "干货型"
    title_style = ""

    for line in spec.split("\n"):
        m = re.match(r"-\s*字数[：:]\s*(.+)", line)
        if m:
            word_count = m.group(1).strip()
        m = re.match(r"-\s*风格[：:]\s*(.+)", line)
        if m:
            style_desc = m.group(1).strip()
        m = re.match(r"-\s*结构[：:]\s*(.+)", line)
        if m:
            structure = m.group(1).strip()
        m = re.match(r"-\s*标题[：:]\s*(.+)", line)
        if m:
            title_style = m.group(1).strip()

    platform_name = PLATFORM_NAME_MAP.get(platform, platform)
    platform_desc = f"{platform_name}平台"

    # Get user style preferences
    user_style = style_cfg.get("style", {})
    genre = user_style.get("genre", "干货型")
    voice = user_style.get("voice", "直接、专业、有观点")

    framework_desc = FRAMEWORK_PROMPTS.get(framework, FRAMEWORK_PROMPTS.get("对比", ""))

    # Deduplication: check history for used angles
    topic_kw = [w for w in re.split(r'[，,、\s]+', topic) if len(w) > 1][:5]
    used = _get_used_angles(topic_kw, platform, history)
    dedup_instruction = _build_dedup_instruction(used)

    system_prompt = f"""你是一个资深内容创作者，擅长为不同平台撰写爆款文章。

你的写作风格：
- 内容领域：{genre}
- 语言基调：{voice}
- 有明确的观点，不模棱两可
- 语言简洁有力，避免套话
- 善用短句增强节奏感
- 适时使用金句增强记忆点

当前任务：为主题「{topic}」撰写一篇适合{platform_desc}的原创文章。

你必须遵循以下规则：
1. 每篇文章必须原创，角度、案例、金句、标题都与其他平台的文章完全不同
2. 严格遵循目标平台的字数、风格、结构要求
3. 使用 Markdown 格式输出
4. 标题用 # 开头（只写一个H1标题）
5. 正文用 ## 分隔章节（4-6 个 H2）
6. {framework_desc}
7. 包含 2-4 条金句（用**金句：**标注）
8. {dedup_instruction}
9. 不要输出任何解释或说明，只输出文章内容"""

    user_prompt = f"""请为主题「{topic}」撰写一篇{platform_desc}文章。

平台要求：
- 平台：{platform_name}
- 字数：{word_count} 字
- 风格：{style_desc}
- 结构：{structure}
"""
    if title_style:
        user_prompt += f"- 标题风格：{title_style}\n"
    user_prompt += f"""
写作框架：{framework}（{framework_desc}）
用户偏好风格：{genre}，{voice}

请直接输出完整的 Markdown 文章，不要包含任何解释或说明文字。"""

    # Temperature variation per platform
    temp_map = {
        "wechat": 0.7,
        "xiaohongshu": 0.8,
        "zhihu": 0.6,
        "baijiahao": 0.7,
        "weibo": 0.9,
        "sohu": 0.6,
        "toutiao": 0.8,
        "qiehao": 0.7,
        "jianshu": 0.7,
        "douban": 0.8,
        "dayu": 0.7,
        "kr36": 0.6,
        "bilibili": 0.8,
        "douyin": 0.9,
        "newsletter": 0.7,
    }
    temperature = temp_map.get(platform, 0.7)

    if seed is not None:
        temperature = min(1.0, temperature + seed * 0.05)

    return generate_text(system_prompt, user_prompt, temperature=temperature, config=config)


def _extract_title(article: str) -> str:
    """Extract H1 title from article."""
    for line in article.split("\n")[:10]:
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def write_for_platforms(
    topic: str,
    platforms: list = None,
    framework: str = "对比",
    config: dict = None,
    save_to_history: bool = True,
) -> dict:
    """
    Write unique articles for multiple platforms.

    If text providers are configured, generates articles via LLM API.
    If no text providers, returns platform specs only (AI assistant writes manually).

    Args:
        topic: The topic/title
        platforms: List of platform keys. If None, uses all available.
        framework: Writing framework
        config: Optional config dict
        save_to_history: Whether to save results to history.yaml for dedup

    Returns:
        Dict of {platform: article_markdown}
    """
    if config is None:
        config = _load_config()

    if platforms is None:
        platforms = list(PLATFORM_SPECS.keys())

    # Load history for deduplication
    history = _load_history()

    # Check if text providers are available
    from text_gen import _build_text_provider_chain
    chain = _build_text_provider_chain(config)
    if not chain:
        # No text API configured - return platform specs for AI assistant to write
        print("  ℹ️  未配置文本生成 API，请查看下方各平台写作要求")
        specs = {}
        for p in platforms:
            spec = PLATFORM_SPECS.get(p, "")
            specs[p] = f"# Platform: {p}\n{spec[:500]}...\n\n[请手动撰写文章]"
        return specs

    # Use LLM API to generate articles (with deduplication)
    results = {}
    for i, platform in enumerate(platforms):
        print(f"  [{i+1}/{len(platforms)}] 正在为 {platform} 生成文章...")
        try:
            article = write_for_platform(topic, platform, framework, seed=i, config=config, history=history)
            results[platform] = article
            
            title = _extract_title(article)
            print(f"  ✅ {platform}: ~{len(article)} 字, 标题: {title[:30]}...")
            
            # Save to history immediately for next platform's dedup
            if save_to_history:
                history_entry = {
                    "date": Path(__file__).parent.parent.name,
                    "title": title,
                    "topic_source": "per-platform",
                    "topic_keywords": [w for w in re.split(r'[，,、\s]+', topic) if len(w) > 1][:5],
                    "platforms": [platform],
                    "framework": framework,
                    "word_count": len(article),
                    "writing_persona": "auto",
                    "dimensions": [],
                    "closing_type": "",
                    "composite_score": 0,
                }
                _save_history(history_entry)
                history.append(history_entry)
        except Exception as e:
            print(f"  ❌ {platform}: {e}")
    return results


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate per-platform articles")
    ap.add_argument("topic", help="Article topic")
    ap.add_argument("--platforms", nargs="+", default=None,
                    help="Platform keys (default: all)")
    ap.add_argument("--framework", default="对比",
                    help="Writing framework")
    args = ap.parse_args()

    results = write_for_platforms(args.topic, args.platforms, args.framework)
    for platform, article in results.items():
        output = Path(f"{platform}.md")
        output.write_text(article, encoding="utf-8")
        print(f"Saved: {output}")
