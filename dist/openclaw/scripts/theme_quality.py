#!/usr/bin/env python3
"""
theme_quality.py — Score and validate a Writer theme file.

Analyzes a YAML theme definition for visual coherence, accessibility,
and WeChat compatibility. Provides suggestions for improvement.

Usage:
    python3 scripts/theme_quality.py themes/professional-clean.yaml
    python3 scripts/theme_quality.py themes/professional-clean.yaml --json
"""

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "toolkit"))
from theme import load_theme


def analyze_theme_colors(theme):
    """Analyze color palette for coherence and accessibility."""
    colors = theme.css_dict.get("colors", {})
    primary = colors.get("primary", "")
    bg = colors.get("background", "#ffffff")
    text = colors.get("text", "#333333")

    issues = []
    suggestions = []

    # Check contrast ratio (simplified)
    def luminance(hex_color):
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def contrast_ratio(c1, c2):
        l1 = luminance(c1)
        l2 = luminance(c2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    ratio = contrast_ratio(text, bg)
    if ratio < 4.5:
        issues.append(f"正文文字与背景对比度不足 (当前 {ratio:.1f}:1，建议 ≥ 4.5:1)")
        suggestions.append("考虑加深文字颜色或调亮背景色")

    if primary:
        primary_ratio = contrast_ratio(primary, bg)
        if primary_ratio < 3.0:
            issues.append(f"主色与背景对比度不足 (当前 {primary_ratio:.1f}:1，建议 ≥ 3.0:1)")
            suggestions.append("主色用于标题和链接，需要更高的可读性")

    # Color count check
    if len(colors) > 10:
        suggestions.append(f"调色板包含 {len(colors)} 种颜色，建议控制在 6-8 种以内以保持一致性")

    # Warm/cool coherence
    def color_temp(hex_color):
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r - b) / 255.0  # positive = warm, negative = cool

    temps = [color_temp(c) for c in colors.values() if len(c.lstrip("#")) == 6]
    if temps:
        avg_temp = sum(temps) / len(temps)
        temp_variance = sum((t - avg_temp) ** 2 for t in temps) / len(temps)
        if temp_variance > 0.3:
            suggestions.append("调色板冷暖色调差异较大，建议统一为暖色调或冷色调")

    return {
        "contrast_ratio": round(ratio, 2),
        "color_count": len(colors),
        "temperature": "warm" if avg_temp > 0 else "cool" if temps else "neutral",
        "issues": issues,
        "suggestions": suggestions,
    }


def analyze_typography(theme):
    """Analyze typography settings for readability."""
    css = theme.css_dict
    issues = []
    suggestions = []

    # Font size hierarchy
    h1_size = _extract_font_size(css, "h1")
    h2_size = _extract_font_size(css, "h2")
    p_size = _extract_font_size(css, "p")

    if h1_size and h2_size and h1_size <= h2_size:
        issues.append("H1 字号应大于 H2")

    if h2_size and p_size and h2_size <= p_size:
        suggestions.append("H2 字号建议略大于正文，以增强层次感")

    # Line height
    line_height = _extract_line_height(css, "p")
    if line_height and line_height < 1.5:
        issues.append(f"行高 {line_height} 过小，建议 ≥ 1.5 以提高可读性")
    elif line_height and line_height > 2.0:
        suggestions.append(f"行高 {line_height} 较大，适合文艺风格，但可能影响阅读密度")

    # Spacing
    margin = _extract_margin(css, "p")
    if margin and margin < 8:
        suggestions.append("段落间距较小，建议增加以提升呼吸感")

    return {
        "font_sizes": {"h1": h1_size, "h2": h2_size, "p": p_size},
        "line_height": line_height,
        "paragraph_margin": margin,
        "issues": issues,
        "suggestions": suggestions,
    }


def _extract_font_size(css_dict, selector):
    """Extract font size in px from CSS dict."""
    key = f"{selector} > *"
    style = css_dict.get(key, "")
    import re
    m = re.search(r"font-size:\s*(\d+(?:\.\d+)?)px", style)
    return float(m.group(1)) if m else None


def _extract_line_height(css_dict, selector):
    """Extract line height from CSS dict."""
    key = f"{selector} > *"
    style = css_dict.get(key, "")
    import re
    m = re.search(r"line-height:\s*(\d+(?:\.\d+)?)", style)
    return float(m.group(1)) if m else None


def _extract_margin(css_dict, selector):
    """Extract bottom margin in px from CSS dict."""
    key = f"{selector} > *"
    style = css_dict.get(key, "")
    import re
    m = re.search(r"margin-bottom:\s*(\d+(?:\.\d+)?)px", style)
    return float(m.group(1)) if m else None


def score_theme(theme):
    """Score a theme from 0-100 based on visual quality."""
    color_analysis = analyze_theme_colors(theme)
    typo_analysis = analyze_typography(theme)

    score = 100

    # Deduct for issues
    score -= len(color_analysis["issues"]) * 10
    score -= len(typo_analysis["issues"]) * 8

    # Bonus for good practices
    if color_analysis["contrast_ratio"] >= 7.0:
        score += 5
    if color_analysis["color_count"] <= 8:
        score += 3
    if typo_analysis.get("line_height") and 1.6 <= typo_analysis["line_height"] <= 1.9:
        score += 3

    return max(0, min(100, score))


def generate_report(theme_name, theme):
    """Generate a full quality report for a theme."""
    color_analysis = analyze_theme_colors(theme)
    typo_analysis = analyze_typography(theme)
    total_score = score_theme(theme)

    report = {
        "theme": theme_name,
        "score": total_score,
        "color_analysis": {
            "contrast_ratio": color_analysis["contrast_ratio"],
            "color_count": color_analysis["color_count"],
            "temperature": color_analysis["temperature"],
            "issues": color_analysis["issues"],
        },
        "typography_analysis": {
            "font_sizes": typo_analysis["font_sizes"],
            "line_height": typo_analysis["line_height"],
            "paragraph_margin": typo_analysis["paragraph_margin"],
            "issues": typo_analysis["issues"],
        },
        "suggestions": color_analysis["suggestions"] + typo_analysis["suggestions"],
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Score and validate a Writer theme")
    parser.add_argument("theme", help="Theme name or path to YAML file")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    try:
        theme = load_theme(args.theme)
    except Exception as e:
        print(f"Error loading theme: {e}", file=sys.stderr)
        sys.exit(1)

    report = generate_report(args.theme, theme)

    if args.json:
        import json
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*50}")
        print(f"Writer 主题质量报告: {report['theme']}")
        print(f"{'='*50}")
        print(f"\n综合评分: {report['score']}/100")
        print(f"\n色彩分析:")
        print(f"  对比度: {report['color_analysis']['contrast_ratio']}:1")
        print(f"  颜色数量: {report['color_analysis']['color_count']}")
        print(f"  色调: {report['color_analysis']['temperature']}")
        if report['color_analysis']['issues']:
            print(f"  问题:")
            for issue in report['color_analysis']['issues']:
                print(f"    ⚠️ {issue}")
        print(f"\n排版分析:")
        sizes = report['typography_analysis']['font_sizes']
        print(f"  字号: H1={sizes.get('h1')}px, H2={sizes.get('h2')}px, 正文={sizes.get('p')}px")
        print(f"  行高: {report['typography_analysis']['line_height']}")
        if report['typography_analysis']['issues']:
            print(f"  问题:")
            for issue in report['typography_analysis']['issues']:
                print(f"    ⚠️ {issue}")
        if report['suggestions']:
            print(f"\n建议:")
            for s in report['suggestions']:
                print(f"  💡 {s}")
        print()


if __name__ == "__main__":
    main()
