#!/usr/bin/env python3
"""
Batch operations for Writer — multi-angle generation and batch export.

Usage:
    python3 scripts/batch_gen.py --topic "AI大模型" --angles 3
    python3 scripts/batch_gen.py --topic "AI大模型" --frameworks 痛点型,清单型
    python3 scripts/batch_gen.py --batch export --input-dir output/batch-xxx
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "toolkit"))
from exporter import export_platform, export_all_platforms


FRAMEWORKS = ["痛点型", "故事型", "清单型", "对比型", "热点解读型", "纯观点型", "复盘型"]

ANGLE_TEMPLATES = {
    "趋势分析": "分析行业发展趋势，展望未来方向",
    "案例拆解": "通过具体案例深度拆解成功/失败原因",
    "实操教程": "手把手教程，包含具体步骤和工具",
    "观点碰撞": "对现有观点进行对比分析，提出新看法",
    "避坑指南": "总结常见错误，给出避坑建议",
    "工具测评": "横向对比多个工具，给出选择建议",
}


def load_config() -> dict:
    for p in [Path.cwd() / "config.yaml", Path(__file__).parent.parent / "config.yaml",
              Path.home() / ".config" / "writer" / "config.yaml"]:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


def load_style() -> dict:
    for p in [Path.cwd() / "style.yaml", Path(__file__).parent.parent / "style.yaml"]:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


def generate_batch_plan(topic: str, num_angles: int = 3, frameworks: list = None):
    """Generate a batch plan with different angles and frameworks."""
    if frameworks:
        selected_frameworks = frameworks
    else:
        selected_frameworks = list(FRAMEWORKS)[:num_angles]

    angles = list(ANGLE_TEMPLATES.items())[:num_angles]

    plan = []
    for i, (fw, (angle_name, angle_desc)) in enumerate(zip(selected_frameworks, angles)):
        plan.append({
            "index": i + 1,
            "topic": topic,
            "angle": angle_name,
            "angle_description": angle_desc,
            "framework": fw,
            "suggested_title": _generate_title(topic, angle_name, fw),
        })

    return plan


def _generate_title(topic: str, angle: str, framework: str) -> str:
    """Generate a suggested title based on angle and framework."""
    title_map = {
        "趋势分析": f"2026{topic}趋势展望：未来3年的5个关键信号",
        "案例拆解": f"深度拆解：{topic}背后的底层逻辑",
        "实操教程": f"{topic}最全指南：从入门到精通",
        "观点碰撞": f"关于{topic}，你可能一直想错了",
        "避坑指南": f"{topic}避坑指南：这8个坑别再踩了",
        "工具测评": f"{topic}工具横评：选对工具效率翻倍",
    }
    return title_map.get(angle, f"关于{topic}，你必须知道的事")


def print_batch_plan(plan):
    """Print batch plan in a human-readable format."""
    print(f"\n{'='*60}")
    print(f"Writer 批量生成计划")
    print(f"{'='*60}")
    print(f"共 {len(plan)} 篇文章：\n")

    for item in plan:
        print(f"  [{item['index']}] {item['angle']}")
        print(f"      框架: {item['framework']}")
        print(f"      建议标题: {item['suggested_title']}")
        print(f"      说明: {item['angle_description']}")
        print()


def save_batch_plan(plan, output_dir):
    """Save batch plan as JSON for agent to process."""
    output_path = Path(output_dir) / "batch_plan.json"
    output_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def batch_export(input_dir, platform, theme="professional-clean"):
    """Batch export all markdown files in a directory to a target platform."""
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    md_files = list(input_path.glob("*.md"))
    if not md_files:
        print(f"No markdown files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    results = {}
    for md_file in md_files:
        md_content = md_file.read_text(encoding="utf-8")
        output_subdir = input_path / md_file.stem

        if platform == "all":
            results[md_file.stem] = export_all_platforms(md_content, str(output_subdir), theme)
        else:
            results[md_file.stem] = export_platform(md_content, platform, str(output_subdir), theme)

        print(f"  Exported: {md_file.stem} -> {output_subdir}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Batch operations for Writer")
    sub = parser.add_subparsers(dest="command", required=True)

    # gen
    p_gen = sub.add_parser("gen", help="Generate batch plan")
    p_gen.add_argument("--topic", required=True, help="Article topic")
    p_gen.add_argument("--angles", type=int, default=3, help="Number of angles to generate")
    p_gen.add_argument("--frameworks", type=str, default="", help="Comma-separated frameworks")
    p_gen.add_argument("--output", default="output", help="Output directory")
    p_gen.add_argument("--json", action="store_true", help="Output JSON plan")

    # export
    p_export = sub.add_parser("export", help="Batch export markdown files")
    p_export.add_argument("--input-dir", required=True, help="Directory with markdown files")
    p_export.add_argument("--platform", required=True, help="Target platform or 'all'")
    p_export.add_argument("--theme", default="professional-clean", help="Theme name")

    args = parser.parse_args()

    if args.command == "gen":
        frameworks = [f.strip() for f in args.frameworks.split(",")] if args.frameworks else None
        plan = generate_batch_plan(args.topic, args.angles, frameworks)

        if args.json:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print_batch_plan(plan)
            output_path = save_batch_plan(plan, args.output)
            print(f"计划已保存: {output_path}")

    elif args.command == "export":
        batch_export(args.input_dir, args.platform, args.theme)


if __name__ == "__main__":
    main()
