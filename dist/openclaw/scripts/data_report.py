#!/usr/bin/env python3
"""
data_report.py — Generate visual data analysis reports from Writer history.

Reads history.yaml and produces an interactive HTML dashboard with:
  - Publishing frequency trends
  - Platform distribution
  - Quality score evolution
  - Framework & persona usage
  - Topic domain breakdown

Usage:
    python3 scripts/data_report.py
    python3 scripts/data_report.py --days 30
    python3 data_report.py --output report.html
    python3 data_report.py --platform wechat
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)


PLATFORM_NAMES = {
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
    "bilibili": "哔哩哔哩",
    "douyin": "抖音",
    "newsletter": "Newsletter",
}

FRAMEWORK_COLORS = {
    "痛点型": "#FF6B6B",
    "故事型": "#4ECDC4",
    "清单型": "#45B7D1",
    "对比型": "#96CEB4",
    "热点解读型": "#FFEAA7",
    "纯观点型": "#DDA0DD",
    "复盘型": "#98D8C8",
}


def load_history(skill_dir):
    history_path = Path(skill_dir) / "history.yaml"
    if not history_path.exists():
        return []
    with open(history_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        return []
    return data


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
    filtered = []
    for r in records:
        dt = parse_date(r.get("date", ""))
        if dt and dt >= cutoff:
            filtered.append(r)
    return filtered


def filter_by_platform(records, platform):
    if not platform:
        return records
    return [r for r in records if platform in r.get("platforms", [])]


def compute_trend_data(records):
    date_counts = {}
    for r in records:
        dt = parse_date(r.get("date", ""))
        if dt:
            key = dt.strftime("%Y-%m-%d")
            date_counts[key] = date_counts.get(key, 0) + 1

    sorted_dates = sorted(date_counts.keys())
    return sorted_dates, [date_counts[d] for d in sorted_dates]


def compute_platform_distribution(records):
    platform_counts = {}
    for r in records:
        for p in r.get("platforms", []):
            platform_counts[p] = platform_counts.get(p, 0) + 1
    return sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)


def compute_quality_trend(records):
    scores = []
    for r in records:
        score = r.get("composite_score")
        if score is not None:
            date = r.get("date", "")
            title = r.get("title", "Untitled")
            scores.append({
                "date": date,
                "score": score,
                "title": title,
            })
    return scores


def compute_framework_usage(records):
    fw_counts = {}
    for r in records:
        fw = r.get("framework", "未知")
        fw_counts[fw] = fw_counts.get(fw, 0) + 1
    return sorted(fw_counts.items(), key=lambda x: x[1], reverse=True)


def compute_persona_usage(records):
    persona_counts = {}
    for r in records:
        p = r.get("writing_persona", "未知")
        persona_counts[p] = persona_counts.get(p, 0) + 1
    return sorted(persona_counts.items(), key=lambda x: x[1], reverse=True)


def compute_topic_distribution(records):
    topic_counts = {}
    for r in records:
        keywords = r.get("topic_keywords", [])
        for kw in keywords:
            topic_counts[kw] = topic_counts.get(kw, 0) + 1
    return sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:15]


def compute_word_count_trend(records):
    wc_data = []
    for r in records:
        wc = r.get("word_count")
        if wc:
            wc_data.append({
                "date": r.get("date", ""),
                "word_count": wc,
                "title": r.get("title", ""),
            })
    return wc_data


def compute_avg_quality(records):
    scores = [r.get("composite_score") for r in records if r.get("composite_score") is not None]
    if not scores:
        return None
    return sum(scores) / len(scores)


def compute_streak(records):
    if not records:
        return 0
    dates = set()
    for r in records:
        dt = parse_date(r.get("date", ""))
        if dt:
            dates.add(dt.strftime("%Y-%m-%d"))

    sorted_dates = sorted(dates, reverse=True)
    if not sorted_dates:
        return 0

    streak = 1
    for i in range(1, len(sorted_dates)):
        curr = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d")
        prev = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
        if (curr - prev).days == 1:
            streak += 1
        else:
            break
    return streak


def generate_html(report_data, output_path):
    dates, counts = report_data["trend"]
    platform_dist = report_data["platform_dist"]
    quality_trend = report_data["quality_trend"]
    framework_usage = report_data["framework_usage"]
    persona_usage = report_data["persona_usage"]
    topic_dist = report_data["topic_dist"]
    word_count_trend = report_data["word_count_trend"]
    stats = report_data["stats"]

    trend_json = json.dumps({"labels": dates, "values": counts}, ensure_ascii=False)
    quality_json = json.dumps(quality_trend, ensure_ascii=False)
    word_count_json = json.dumps(word_count_trend, ensure_ascii=False)

    platform_labels = json.dumps([PLATFORM_NAMES.get(p, p) for p, _ in platform_dist], ensure_ascii=False)
    platform_values = json.dumps([v for _, v in platform_dist], ensure_ascii=False)

    framework_labels = json.dumps([fw for fw, _ in framework_usage], ensure_ascii=False)
    framework_values = json.dumps([v for _, v in framework_usage], ensure_ascii=False)
    framework_colors = json.dumps(
        [FRAMEWORK_COLORS.get(fw, "#888") for fw, _ in framework_usage], ensure_ascii=False
    )

    persona_labels = json.dumps([p for p, _ in persona_usage], ensure_ascii=False)
    persona_values = json.dumps([v for _, v in persona_usage], ensure_ascii=False)

    topic_labels = json.dumps([t for t, _ in topic_dist], ensure_ascii=False)
    topic_values = json.dumps([v for _, v in topic_dist], ensure_ascii=False)

    avg_score = stats.get("avg_quality")
    avg_score_display = f"{avg_score:.1f}" if avg_score is not None else "暂无数据"
    quality_status = "优秀" if (avg_score is not None and avg_score < 30) else \
                     "良好" if (avg_score is not None and avg_score < 50) else \
                     "需改进" if avg_score is not None else ""
    quality_color = "#52c41a" if avg_score is not None and avg_score < 30 else \
                    "#faad14" if avg_score is not None and avg_score < 50 else \
                    "#ff4d4f" if avg_score is not None else "#999"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Writer 数据报告</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #f5f7fa;
    color: #333;
    line-height: 1.6;
    padding: 24px;
  }}
  .header {{
    text-align: center;
    margin-bottom: 32px;
  }}
  .header h1 {{
    font-size: 28px;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 8px;
  }}
  .header p {{
    color: #666;
    font-size: 14px;
  }}
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
  }}
  .stat-card {{
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    text-align: center;
  }}
  .stat-card .value {{
    font-size: 32px;
    font-weight: 700;
    color: #1a1a2e;
  }}
  .stat-card .label {{
    font-size: 13px;
    color: #888;
    margin-top: 4px;
  }}
  .stat-card .sub {{
    font-size: 12px;
    margin-top: 6px;
    padding: 2px 8px;
    border-radius: 4px;
    display: inline-block;
  }}
  .charts-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
    gap: 20px;
    margin-bottom: 24px;
  }}
  .chart-card {{
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  .chart-card h3 {{
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    color: #1a1a2e;
  }}
  .chart-container {{
    position: relative;
    height: 280px;
  }}
  .article-list {{
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  .article-list h3 {{
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    color: #1a1a2e;
  }}
  .article-table {{
    width: 100%;
    border-collapse: collapse;
  }}
  .article-table th, .article-table td {{
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid #f0f0f0;
    font-size: 13px;
  }}
  .article-table th {{
    color: #888;
    font-weight: 500;
  }}
  .article-table tr:hover {{
    background: #fafafa;
  }}
  .score-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
  }}
  .score-good {{ background: #f6ffed; color: #52c41a; }}
  .score-ok {{ background: #fffbe6; color: #faad14; }}
  .score-bad {{ background: #fff2f0; color: #ff4d4f; }}
  .footer {{
    text-align: center;
    margin-top: 40px;
    color: #999;
    font-size: 12px;
  }}
</style>
</head>
<body>

<div class="header">
  <h1>Writer 数据报告</h1>
  <p>生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")} | 共分析 {stats["total_articles"]} 篇文章</p>
</div>

<div class="stats-grid">
  <div class="stat-card">
    <div class="value">{stats["total_articles"]}</div>
    <div class="label">总发文数</div>
  </div>
  <div class="stat-card">
    <div class="value">{stats["streak"]}</div>
    <div class="label">连续发文天数</div>
  </div>
  <div class="stat-card">
    <div class="value" style="color: {quality_color}">{avg_score_display}</div>
    <div class="label">平均质量分数</div>
    <div class="sub" style="background: {quality_color}22; color: {quality_color}">{quality_status}</div>
  </div>
  <div class="stat-card">
    <div class="value">{stats["total_platforms"]}</div>
    <div class="label">覆盖平台数</div>
  </div>
  <div class="stat-card">
    <div class="value">{stats["total_words"]}</div>
    <div class="label">总字数</div>
  </div>
  <div class="stat-card">
    <div class="value">{stats["avg_words"]}</div>
    <div class="label">平均字数</div>
  </div>
</div>

<div class="charts-grid">
  <div class="chart-card">
    <h3>发文趋势</h3>
    <div class="chart-container">
      <canvas id="trendChart"></canvas>
    </div>
  </div>
  <div class="chart-card">
    <h3>平台分布</h3>
    <div class="chart-container">
      <canvas id="platformChart"></canvas>
    </div>
  </div>
  <div class="chart-card">
    <h3>质量演变</h3>
    <div class="chart-container">
      <canvas id="qualityChart"></canvas>
    </div>
  </div>
  <div class="chart-card">
    <h3>字数趋势</h3>
    <div class="chart-container">
      <canvas id="wordCountChart"></canvas>
    </div>
  </div>
</div>

<div class="charts-grid">
  <div class="chart-card">
    <h3>框架使用分布</h3>
    <div class="chart-container">
      <canvas id="frameworkChart"></canvas>
    </div>
  </div>
  <div class="chart-card">
    <h3>写作人格分布</h3>
    <div class="chart-container">
      <canvas id="personaChart"></canvas>
    </div>
  </div>
  <div class="chart-card">
    <h3>热门话题 TOP 15</h3>
    <div class="chart-container">
      <canvas id="topicChart"></canvas>
    </div>
  </div>
</div>

<div class="article-list">
  <h3>文章列表</h3>
  <table class="article-table">
    <thead>
      <tr>
        <th>日期</th>
        <th>标题</th>
        <th>平台</th>
        <th>框架</th>
        <th>字数</th>
        <th>质量分</th>
      </tr>
    </thead>
    <tbody>
"""

    for r in report_data.get("articles", []):
        date = r.get("date", "-")
        title = r.get("title", "-")
        platforms = ", ".join([PLATFORM_NAMES.get(p, p) for p in r.get("platforms", [])])
        framework = r.get("framework", "-")
        word_count = r.get("word_count", "-")
        score = r.get("composite_score")
        if score is not None:
            score_display = f'<span class="score-badge {"score-good" if score < 30 else "score-ok" if score < 50 else "score-bad"}">{score:.0f}</span>'
        else:
            score_display = "-"
        html += f"""      <tr>
        <td>{date}</td>
        <td>{title}</td>
        <td>{platforms}</td>
        <td>{framework}</td>
        <td>{word_count}</td>
        <td>{score_display}</td>
      </tr>
"""

    html += """    </tbody>
  </table>
</div>

<div class="footer">
  Generated by Writer Data Report
</div>

<script>
const trendData = """ + trend_json + """;
new Chart(document.getElementById('trendChart'), {
  type: 'line',
  data: {
    labels: trendData.labels,
    datasets: [{
      label: '发文数',
      data: trendData.values,
      borderColor: '#45B7D1',
      backgroundColor: 'rgba(69,183,209,0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 3,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
  }
});

const platformLabels = """ + platform_labels + """;
const platformValues = """ + platform_values + """;
new Chart(document.getElementById('platformChart'), {
  type: 'doughnut',
  data: {
    labels: platformLabels,
    datasets: [{
      data: platformValues,
      backgroundColor: ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD','#98D8C8','#FF9FF3','#54A0FF','#5F27CD','#01D2D2','#FFC300','#FF6348','#7BED9F','#70A1FF'],
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } } }
  }
});

const qualityData = """ + quality_json + """;
new Chart(document.getElementById('qualityChart'), {
  type: 'line',
  data: {
    labels: qualityData.map(d => d.date),
    datasets: [{
      label: '质量分数',
      data: qualityData.map(d => d.score),
      borderColor: '#FF6B6B',
      backgroundColor: 'rgba(255,107,107,0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 4,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items) => qualityData[items[0].dataIndex].title,
          label: (item) => '质量分: ' + item.raw.toFixed(0) + ' (越低越好)'
        }
      }
    },
    scales: { y: { min: 0, max: 100 } }
  }
});

const wcData = """ + word_count_json + """;
new Chart(document.getElementById('wordCountChart'), {
  type: 'bar',
  data: {
    labels: wcData.map(d => d.date),
    datasets: [{
      label: '字数',
      data: wcData.map(d => d.word_count),
      backgroundColor: 'rgba(150,206,180,0.7)',
      borderRadius: 4,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items) => wcData[items[0].dataIndex].title,
          label: (item) => item.raw + ' 字'
        }
      }
    },
    scales: { y: { beginAtZero: true } }
  }
});

const fwLabels = """ + framework_labels + """;
const fwValues = """ + framework_values + """;
const fwColors = """ + framework_colors + """;
new Chart(document.getElementById('frameworkChart'), {
  type: 'bar',
  data: {
    labels: fwLabels,
    datasets: [{
      data: fwValues,
      backgroundColor: fwColors,
      borderRadius: 4,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } }
  }
});

const pLabels = """ + persona_labels + """;
const pValues = """ + persona_values + """;
new Chart(document.getElementById('personaChart'), {
  type: 'polarArea',
  data: {
    labels: pLabels,
    datasets: [{
      data: pValues,
      backgroundColor: ['rgba(255,107,107,0.7)','rgba(78,205,196,0.7)','rgba(69,183,209,0.7)','rgba(150,206,180,0.7)','rgba(255,234,167,0.7)'],
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } } }
  }
});

const tLabels = """ + topic_labels + """;
const tValues = """ + topic_values + """;
new Chart(document.getElementById('topicChart'), {
  type: 'bar',
  data: {
    labels: tLabels,
    datasets: [{
      label: '使用次数',
      data: tValues,
      backgroundColor: 'rgba(221,160,221,0.7)',
      borderRadius: 4,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } }
  }
});
</script>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Writer data analysis report generator")
    parser.add_argument("--days", type=int, default=None, help="Only include articles from last N days")
    parser.add_argument("--platform", type=str, default=None, help="Filter by platform (e.g., wechat)")
    parser.add_argument("--output", type=str, default=None, help="Output HTML file path")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of HTML")
    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent
    records = load_history(skill_dir)

    if not records:
        print("No history found. Run some articles first to generate data.")
        sys.exit(0)

    if args.days:
        records = filter_by_days(records, args.days)
    if args.platform:
        records = filter_by_platform(records, args.platform)

    records.sort(key=lambda r: r.get("date", ""))

    trend_dates, trend_counts = compute_trend_data(records)
    platform_dist = compute_platform_distribution(records)
    quality_trend = compute_quality_trend(records)
    framework_usage = compute_framework_usage(records)
    persona_usage = compute_persona_usage(records)
    topic_dist = compute_topic_distribution(records)
    word_count_trend = compute_word_count_trend(records)

    total_words = sum(r.get("word_count", 0) for r in records if r.get("word_count"))
    avg_words = int(total_words / len([r for r in records if r.get("word_count")])) if records else 0
    all_platforms = set()
    for r in records:
        all_platforms.update(r.get("platforms", []))

    avg_quality = compute_avg_quality(records)
    streak = compute_streak(records)

    stats = {
        "total_articles": len(records),
        "streak": streak,
        "avg_quality": avg_quality,
        "total_platforms": len(all_platforms),
        "total_words": total_words,
        "avg_words": avg_words,
    }

    report_data = {
        "trend": (trend_dates, trend_counts),
        "platform_dist": platform_dist,
        "quality_trend": quality_trend,
        "framework_usage": framework_usage,
        "persona_usage": persona_usage,
        "topic_dist": topic_dist,
        "word_count_trend": word_count_trend,
        "stats": stats,
        "articles": records,
    }

    if args.json:
        json_output = {
            "stats": stats,
            "trend": {"dates": trend_dates, "counts": trend_counts},
            "platform_distribution": dict(platform_dist),
            "quality_trend": quality_trend,
            "framework_usage": dict(framework_usage),
            "persona_usage": dict(persona_usage),
            "topic_distribution": dict(topic_dist),
            "articles": records,
        }
        print(json.dumps(json_output, ensure_ascii=False, indent=2))
        return

    output_path = args.output or str(skill_dir / "output" / "data_report.html")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    generate_html(report_data, output_path)

    print(f"Report generated: {output_path}")
    print(f"Total articles: {stats['total_articles']}")
    print(f"Date range: {trend_dates[0] if trend_dates else 'N/A'} ~ {trend_dates[-1] if trend_dates else 'N/A'}")
    print(f"Platforms: {', '.join([PLATFORM_NAMES.get(p, p) for p, _ in platform_dist[:5]])}")
    if avg_quality is not None:
        print(f"Average quality score: {avg_quality:.1f} (lower is better)")


if __name__ == "__main__":
    main()
