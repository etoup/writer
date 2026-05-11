#!/usr/bin/env python3
"""
wechat_review.py — Generate a data review report for WeChat Official Account articles.

Reads history.yaml and generates a markdown report with:
  - Article performance summary
  - Title strategy analysis
  - Framework effectiveness
  - Quality trends and recommendations

Usage:
    python3 scripts/wechat_review.py
    python3 scripts/wechat_review.py --days 30
    python3 scripts/wechat_review.py --output review.md
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)


def load_history(skill_dir):
    history_path = Path(skill_dir) / "history.yaml"
    if not history_path.exists():
        return []
    with open(history_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        return []
    return [r for r in data if "wechat" in r.get("platforms", [])]


def parse_date(date_str):
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def filter_by_days(records, days):
    if days is None:
        return records
    cutoff = datetime.now() - timedelta(days=days)
    return [r for r in records if parse_date(r.get("date", "")) and parse_date(r.get("date", "")) >= cutoff]


def analyze_titles(records):
    titles = [(r.get("title", ""), r.get("composite_score")) for r in records if r.get("title")]
    if not titles:
        return []

    strategies = {
        "数字型": 0,
        "疑问型": 0,
        "观点型": 0,
        "故事型": 0,
        "热点型": 0,
        "教程型": 0,
    }

    for title, _ in titles:
        if any(c.isdigit() for c in title[:10]):
            strategies["数字型"] += 1
        elif "？" in title or "?" in title:
            strategies["疑问型"] += 1
        elif any(w in title for w in ["为什么", "如何", "怎样", "揭秘", "真相"]):
            strategies["教程型"] += 1
        elif any(w in title for w in ["我", "我们", "我的", "经历", "心得"]):
            strategies["故事型"] += 1
        elif any(w in title for w in ["趋势", "爆", "热", "最新", "突发", "重磅"]):
            strategies["热点型"] += 1
        else:
            strategies["观点型"] += 1

    return sorted(strategies.items(), key=lambda x: x[1], reverse=True)


def analyze_framework_performance(records):
    fw_scores = {}
    for r in records:
        fw = r.get("framework", "未知")
        score = r.get("composite_score")
        if score is not None:
            if fw not in fw_scores:
                fw_scores[fw] = []
            fw_scores[fw].append(score)

    results = []
    for fw, scores in fw_scores.items():
        avg = sum(scores) / len(scores)
        results.append({
            "framework": fw,
            "count": len(scores),
            "avg_score": avg,
            "best_score": min(scores),
        })

    return sorted(results, key=lambda x: x["avg_score"])


def analyze_word_count(records):
    wc_data = []
    for r in records:
        wc = r.get("word_count")
        if wc:
            wc_data.append(wc)

    if not wc_data:
        return {}

    return {
        "min": min(wc_data),
        "max": max(wc_data),
        "avg": int(sum(wc_data) / len(wc_data)),
        "median": sorted(wc_data)[len(wc_data) // 2],
    }


def generate_recommendations(records):
    recommendations = []

    if len(records) >= 3:
        scores = [r.get("composite_score") for r in records if r.get("composite_score") is not None]
        if scores:
            recent = scores[-3:]
            older = scores[:-3] if len(scores) > 3 else scores
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)

            if recent_avg < older_avg:
                recommendations.append("质量分数呈下降趋势，建议回顾最近文章的框架和 persona 选择")
            elif recent_avg > older_avg:
                recommendations.append("质量分数呈上升趋势，继续保持当前写作策略")
            else:
                recommendations.append("质量分数保持稳定，可尝试新框架或 persona 打破瓶颈")

    fw_perf = analyze_framework_performance(records)
    if fw_perf:
        best_fw = fw_perf[0]
        recommendations.append(f"表现最好的框架是「{best_fw['framework']}」（均分 {best_fw['avg_score']:.0f}）")

    wc_stats = analyze_word_count(records)
    if wc_stats:
        recommendations.append(f"平均字数为 {wc_stats['avg']} 字，建议保持在 {wc_stats['avg'] - 200}~{wc_stats['avg'] + 200} 字区间")

    title_strategies = analyze_titles(records)
    if title_strategies:
        top_strategy = title_strategies[0][0]
        recommendations.append(f"最常使用的标题策略是「{top_strategy}」，可尝试其他策略增加多样性")

    if not recommendations:
        recommendations.append("数据不足以生成建议，请发布更多文章后再试")

    return recommendations


def generate_markdown(records, output_path):
    total = len(records)
    wc_stats = analyze_word_count(records)
    fw_perf = analyze_framework_performance(records)
    title_strategies = analyze_titles(records)
    recommendations = generate_recommendations(records)

    avg_score = None
    scores = [r.get("composite_score") for r in records if r.get("composite_score") is not None]
    if scores:
        avg_score = sum(scores) / len(scores)

    md = f"""# 公众号数据复盘报告

**生成时间**：{datetime.now().strftime("%Y-%m-%d %H:%M")}
**分析范围**：共 {total} 篇公众号文章

---

## 一、概览

| 指标 | 数值 |
|------|------|
| 发文总数 | {total} 篇 |
| 平均质量分 | {avg_score:.1f}（越低越好） if avg_score is not None else 暂无数据 |
| 平均字数 | {wc_stats.get('avg', '暂无数据')} 字 |
| 字数范围 | {wc_stats.get('min', '暂无数据')} ~ {wc_stats.get('max', '暂无数据')} 字 |

---

## 二、标题策略分析

| 策略 | 使用次数 |
|------|---------|
"""

    for strategy, count in title_strategies:
        md += f"| {strategy} | {count} |\n"

    md += """
---

## 三、框架效果对比

| 框架 | 使用次数 | 平均质量分 | 最佳分数 |
|------|---------|-----------|---------|
"""

    for fw in fw_perf:
        md += f"| {fw['framework']} | {fw['count']} | {fw['avg_score']:.0f} | {fw['best_score']:.0f} |\n"

    md += """
---

## 四、文章列表

| 日期 | 标题 | 框架 | 字数 | 质量分 |
|------|------|------|------|--------|
"""

    for r in sorted(records, key=lambda x: x.get("date", ""), reverse=True):
        date = r.get("date", "-")
        title = r.get("title", "-")
        framework = r.get("framework", "-")
        wc = r.get("word_count", "-")
        score = r.get("composite_score")
        score_display = f"{score:.0f}" if score is not None else "-"
        md += f"| {date} | {title} | {framework} | {wc} | {score_display} |\n"

    md += """
---

## 五、优化建议

"""

    for i, rec in enumerate(recommendations, 1):
        md += f"{i}. {rec}\n"

    md += f"""
---

## 六、下一步行动

1. **选题优化**：参考框架效果对比，优先使用表现好的框架
2. **标题优化**：尝试使用频率较低的标题策略，增加多样性
3. **质量提升**：关注质量分数较高的文章，分析其共同特征
4. **持续跟踪**：建议每发布 5-10 篇文章后重新生成此报告

---

*报告由 Writer 自动生成*
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="WeChat Official Account data review tool")
    parser.add_argument("--days", type=int, default=None, help="Only analyze articles from last N days")
    parser.add_argument("--output", type=str, default=None, help="Output markdown file path")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent
    records = load_history(skill_dir)

    if not records:
        print("No WeChat articles found in history. Run some articles with wechat platform first.")
        sys.exit(0)

    if args.days:
        records = filter_by_days(records, args.days)

    records.sort(key=lambda r: r.get("date", ""))

    if args.json:
        output = {
            "total_articles": len(records),
            "title_strategies": dict(analyze_titles(records)),
            "framework_performance": analyze_framework_performance(records),
            "word_count_stats": analyze_word_count(records),
            "recommendations": generate_recommendations(records),
            "articles": records,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    output_path = args.output or str(skill_dir / "output" / "wechat_review.md")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    generate_markdown(records, output_path)

    print(f"Review report generated: {output_path}")
    print(f"Analyzed {len(records)} WeChat articles")


if __name__ == "__main__":
    main()
