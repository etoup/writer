#!/usr/bin/env python3
"""
article_diagnose.py — Generate a detailed diagnostic report for a Writer article.

Combines humanness score with content structure analysis, SEO evaluation,
and platform-specific checks. Outputs actionable suggestions.

Usage:
    python3 scripts/article_diagnose.py article.md
    python3 scripts/article_diagnose.py article.md --json
    python3 scripts/article_diagnose.py article.md --platform wechat
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import humanness_score as hs


def analyze_structure(text):
    """Analyze article structure for readability and flow."""
    lines = text.split("\n")

    headings = [l for l in lines if l.startswith("##")]
    h1s = [l for l in lines if l.startswith("# ") and not l.startswith("##")]
    paragraphs = [l for l in lines if l.strip() and not l.startswith("#") and not l.startswith("-") and not l.startswith(">") and not l.startswith("!")]

    issues = []
    suggestions = []

    # H1 check
    if len(h1s) == 0:
        issues.append("缺少 H1 标题")
    elif len(h1s) > 1:
        issues.append("存在多个 H1 标题，建议只保留一个")

    # H1 length
    if h1s:
        h1_text = h1s[0].lstrip("# ").strip()
        h1_len = len(re.sub(r'[^\u4e00-\u9fff]', '', h1_text))
        if h1_len < 15:
            suggestions.append(f"H1 标题较短（{h1_len}字），建议 20-28 字以获得更好的搜索权重")
        elif h1_len > 35:
            suggestions.append(f"H1 标题较长（{h1_len}字），建议精简到 28 字以内")

    # Heading hierarchy
    if len(headings) < 3:
        suggestions.append("文章段落较少（{} 个 H2），建议至少 4-6 个 H2 以提升可读性".format(len(headings)))

    # Paragraph length distribution
    para_lengths = [len(p.strip()) for p in paragraphs if len(p.strip()) > 0]
    if para_lengths:
        avg_len = sum(para_lengths) / len(para_lengths)
        max_len = max(para_lengths)
        if max_len > 500:
            issues.append("存在超长段落（{} 字），建议拆分为 2-3 段".format(max_len))
        if avg_len > 200:
            suggestions.append("平均段落长度较长（{} 字），建议多使用短句和分段".format(int(avg_len)))

    # Check for consecutive similar-length paragraphs
    if len(para_lengths) >= 3:
        similar_runs = 0
        for i in range(len(para_lengths) - 2):
            if abs(para_lengths[i] - para_lengths[i+1]) < 10 and abs(para_lengths[i+1] - para_lengths[i+2]) < 10:
                similar_runs += 1
        if similar_runs > 0:
            suggestions.append("存在连续长度相近的段落（{} 处），建议增加长短变化以提升节奏感".format(similar_runs))

    return {
        "heading_count": len(headings),
        "h1_title": h1s[0].strip() if h1s else None,
        "h1_length": len(re.sub(r'[^\u4e00-\u9fff]', '', h1s[0].lstrip("# ").strip())) if h1s else 0,
        "paragraph_count": len(paragraphs),
        "avg_paragraph_length": int(sum(para_lengths) / len(para_lengths)) if para_lengths else 0,
        "issues": issues,
        "suggestions": suggestions,
    }


def analyze_seo(text, platform="wechat"):
    """Analyze SEO optimization for the article."""
    lines = text.split("\n")
    h1 = ""
    for line in lines:
        if line.startswith("# ") and not line.startswith("##"):
            h1 = line.lstrip("# ").strip()
            break

    issues = []
    suggestions = []

    # Keyword density (simplified)
    words = re.findall(r'[\u4e00-\u9fff]+', text)
    total_chars = len(words)

    if total_chars > 0:
        # Check for keyword repetition
        word_freq = {}
        for w in words:
            if len(w) >= 2:
                word_freq[w] = word_freq.get(w, 0) + 1

        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Check if any keyword is over-used
        for kw, freq in top_keywords:
            density = freq / total_chars
            if density > 0.05:
                suggestions.append(f"关键词「{kw}」出现频率过高（{density*100:.1f}%），建议降低到 2-3%")

    # Platform-specific checks
    if platform == "wechat":
        if len(h1) > 64:
            issues.append("微信标题过长，可能导致显示截断")
        elif len(h1) < 10:
            suggestions.append("微信标题过短，不利于搜索和分享")

    elif platform == "xiaohongshu":
        if len(text) > 3000:
            suggestions.append("小红书正文建议控制在 1000 字以内，当前内容较长")
        # Check for emoji
        emoji_count = len(re.findall(r'[\U0001F300-\U0001F9FF\u2600-\u27BF]', text))
        if emoji_count < 3:
            suggestions.append("小红书建议适当使用 emoji 增强可读性（当前 {} 个）".format(emoji_count))

    elif platform == "zhihu":
        if len(text) < 1500:
            suggestions.append("知乎文章建议 2000 字以上以获得更好的推荐权重")

    return {
        "title": h1,
        "title_length": len(h1),
        "total_characters": total_chars,
        "top_keywords": [{"word": w, "count": c} for w, c in top_keywords[:5]] if total_chars > 0 else [],
        "issues": issues,
        "suggestions": suggestions,
    }


def analyze_readability(text):
    """Analyze reading difficulty and engagement factors."""
    sentences = re.split(r'[。！？!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return {"score": 0, "issues": [], "suggestions": []}

    # Sentence length variance
    sent_lengths = [len(s) for s in sentences]
    avg_len = sum(sent_lengths) / len(sent_lengths)
    variance = sum((l - avg_len) ** 2 for l in sent_lengths) / len(sent_lengths)

    issues = []
    suggestions = []

    if variance < 50:
        issues.append("句长方差过低，文章节奏感不足")
    elif variance > 400:
        suggestions.append("句长方差较大，部分句子可能过长，注意可读性")

    # Check for opening hook
    first_3 = text[:150]
    hook_indicators = ["其实", "说实话", "你有没有", "为什么", "如果", "想象一下", "先问一个问题"]
    has_hook = any(indicator in first_3 for indicator in hook_indicators)

    if not has_hook:
        suggestions.append("开头缺少钩子，建议在前 3 句制造悬念/冲突/好奇心")

    # Check for golden quotes (short impactful sentences)
    golden_quotes = [s for s in sentences if 8 <= len(s) <= 20 and ('不是' in s or '就是' in s or '才是' in s)]

    return {
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_len, 1),
        "sentence_variance": round(variance, 1),
        "has_opening_hook": has_hook,
        "golden_quotes_count": len(golden_quotes),
        "issues": issues,
        "suggestions": suggestions,
    }


def generate_full_report(text, platform="wechat", include_humanness=True):
    """Generate a comprehensive diagnostic report."""
    report = {}

    if include_humanness:
        result = hs.analyze_file(Path("/tmp/dummy.md"), text)
        report["humanness_score"] = result

    report["structure"] = analyze_structure(text)
    report["seo"] = analyze_seo(text, platform)
    report["readability"] = analyze_readability(text)

    # Calculate overall quality score
    total_issues = (
        len(report["structure"].get("issues", [])) +
        len(report.get("humanness_score", {}).get("issues", [])) +
        len(report["readability"].get("issues", []))
    )

    total_suggestions = (
        len(report["structure"].get("suggestions", [])) +
        len(report["seo"].get("suggestions", [])) +
        len(report["readability"].get("suggestions", []))
    )

    report["summary"] = {
        "total_issues": total_issues,
        "total_suggestions": total_suggestions,
        "overall_rating": "优秀" if total_issues == 0 else "良好" if total_issues <= 2 else "需改进",
    }

    return report


def format_report_human(report):
    """Format the report for human reading."""
    lines = []
    lines.append("=" * 50)
    lines.append("Writer 文章诊断报告")
    lines.append("=" * 50)

    # Overall
    summary = report.get("summary", {})
    lines.append(f"\n总体评价: {summary.get('overall_rating', 'N/A')}")
    lines.append(f"问题数: {summary.get('total_issues', 0)}")
    lines.append(f"建议数: {summary.get('total_suggestions', 0)}")

    # Humanness score
    if "humanness_score" in report:
        hs_data = report["humanness_score"]
        composite = hs_data.get("composite_score", "N/A")
        lines.append(f"\nAI 痕迹评分: {composite}/100（越低越好）")
        if isinstance(composite, (int, float)) and composite < 30:
            lines.append("✅ 文章读起来自然，AI 痕迹不明显")
        elif isinstance(composite, (int, float)) and composite < 50:
            lines.append("⚠️ 部分段落有 AI 写作特征，建议优化")
        else:
            lines.append("❌ AI 痕迹较重，建议重点修改")

    # Structure
    struct = report.get("structure", {})
    lines.append("\n📐 结构分析:")
    lines.append(f"  H1 标题: {struct.get('h1_title', '无')}")
    lines.append(f"  H2 段落: {struct.get('heading_count', 0)} 个")
    lines.append(f"  总段落: {struct.get('paragraph_count', 0)} 个")
    if struct.get("issues"):
        lines.append("  问题:")
        for issue in struct["issues"]:
            lines.append(f"    ❌ {issue}")

    # SEO
    seo = report.get("seo", {})
    lines.append("\n🔍 SEO 分析:")
    lines.append(f"  标题长度: {seo.get('title_length', 0)} 字")
    lines.append(f"  总字数: {seo.get('total_characters', 0)} 字")
    if seo.get("top_keywords"):
        kw_str = ", ".join([f"{kw['word']}({kw['count']})" for kw in seo["top_keywords"][:5]])
        lines.append(f"  高频词: {kw_str}")
    if seo.get("issues"):
        lines.append("  问题:")
        for issue in seo["issues"]:
            lines.append(f"    ❌ {issue}")

    # Readability
    read = report.get("readability", {})
    lines.append("\n📖 可读性分析:")
    lines.append(f"  句子数: {read.get('sentence_count', 0)}")
    lines.append(f"  平均句长: {read.get('avg_sentence_length', 0)} 字")
    lines.append(f"  句长方差: {read.get('sentence_variance', 0)}")
    lines.append(f"  开头钩子: {'✅ 有' if read.get('has_opening_hook') else '❌ 无'}")
    lines.append(f"  金句数量: {read.get('golden_quotes_count', 0)}")
    if read.get("issues"):
        lines.append("  问题:")
        for issue in read["issues"]:
            lines.append(f"    ❌ {issue}")

    # All suggestions
    all_suggestions = []
    for section in ["structure", "seo", "readability"]:
        if section in report and report[section].get("suggestions"):
            all_suggestions.extend(report[section]["suggestions"])

    if all_suggestions:
        lines.append("\n💡 优化建议:")
        for i, s in enumerate(all_suggestions, 1):
            lines.append(f"  {i}. {s}")

    lines.append("\n" + "=" * 50)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Diagnostic report for Writer articles")
    parser.add_argument("input", help="Markdown file path")
    parser.add_argument("--platform", default="wechat", help="Target platform (wechat/xiaohongshu/zhihu)")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")

    try:
        report = generate_full_report(text, args.platform)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_report_human(report))


if __name__ == "__main__":
    main()
