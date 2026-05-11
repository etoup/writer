#!/usr/bin/env python3
"""
learn_edits.py — Learn from user's edits to improve future drafts.

Compares the original AI-generated article with the user's edited version,
extracts preference rules, and updates the playbook.

Usage:
    python3 scripts/learn_edits.py original.md edited.md
    python3 scripts/learn_edits.py --from-wechat  # sync from WeChat drafts
"""

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

PLAYBOOK_PATH = Path(__file__).parent.parent / "playbook.md"
HISTORY_PATH = Path(__file__).parent.parent / "history.yaml"
LESSONS_DIR = Path(__file__).parent.parent / "lessons"


def extract_sentences(text):
    """Split text into sentences for comparison."""
    # Split by Chinese/English sentence boundaries
    sentences = re.split(r'(?<=[。！？!?])|(?<=[\n])', text)
    return [s.strip() for s in sentences if s.strip()]


def compute_diff_stats(original: str, edited: str) -> dict:
    """Compute statistics about the differences between original and edited."""
    orig_sents = extract_sentences(original)
    edit_sents = extract_sentences(edited)

    # Line-level diff
    orig_lines = original.split("\n")
    edit_lines = edited.split("\n")

    differ = difflib.Differ()
    diff = list(differ.compare(orig_lines, edit_lines))

    added = [line[2:] for line in diff if line.startswith("+ ")]
    removed = [line[2:] for line in diff if line.startswith("- ")]

    # Character-level stats
    orig_chars = len(original)
    edit_chars = len(edited)
    char_diff = edit_chars - orig_chars

    # Word frequency changes
    orig_words = Counter(re.findall(r'[\u4e00-\u9fff]+', original))
    edit_words = Counter(re.findall(r'[\u4e00-\u9fff]+', edited))

    added_words = edit_words - orig_words
    removed_words = orig_words - edit_words

    return {
        "original_sentences": len(orig_sents),
        "edited_sentences": len(edit_sents),
        "original_chars": orig_chars,
        "edited_chars": edit_chars,
        "char_diff": char_diff,
        "lines_added": len(added),
        "lines_removed": len(removed),
        "top_added_words": dict(added_words.most_common(20)),
        "top_removed_words": dict(removed_words.most_common(20)),
        "edit_ratio": abs(char_diff) / orig_chars if orig_chars > 0 else 0,
    }


def extract_preference_rules(stats: dict, original: str, edited: str) -> list[dict]:
    """Extract actionable preference rules from the edit comparison."""
    rules = []

    # Rule 1: Word preference changes
    if stats["top_removed_words"]:
        for word, count in list(stats["top_removed_words"].items())[:5]:
            if count >= 3:
                rules.append({
                    "type": "avoid_word",
                    "word": word,
                    "confidence": min(count * 2, 10),
                    "description": f"用户删除了「{word}」{count} 次，可能不喜欢这个词",
                })

    if stats["top_added_words"]:
        for word, count in list(stats["top_added_words"].items())[:5]:
            if count >= 2:
                rules.append({
                    "type": "prefer_word",
                    "word": word,
                    "confidence": min(count * 2, 10),
                    "description": f"用户多次使用「{word}」，可能偏好这个表达",
                })

    # Rule 2: Length preference
    if stats["edit_ratio"] > 0.3:
        if stats["char_diff"] > 0:
            rules.append({
                "type": "length_preference",
                "direction": "longer",
                "confidence": 6,
                "description": f"用户增加了 {stats['char_diff']} 字，偏好更详细的内容",
            })
        else:
            rules.append({
                "type": "length_preference",
                "direction": "shorter",
                "confidence": 6,
                "description": f"用户删除了 {abs(stats['char_diff'])} 字，偏好更简洁的内容",
            })

    # Rule 3: Structural changes
    orig_headings = len(re.findall(r'^##', original, re.MULTILINE))
    edit_headings = len(re.findall(r'^##', edited, re.MULTILINE))
    if edit_headings > orig_headings:
        rules.append({
            "type": "structure_preference",
            "direction": "more_headings",
            "confidence": 5,
            "description": "用户增加了小标题，偏好更多分段",
        })
    elif edit_headings < orig_headings:
        rules.append({
            "type": "structure_preference",
            "direction": "fewer_headings",
            "confidence": 5,
            "description": "用户减少了小标题，偏好更少的分段",
        })

    # Rule 4: Emoji/tone changes
    orig_emojis = len(re.findall(r'[\U0001F300-\U0001F9FF\u2600-\u27BF]', original))
    edit_emojis = len(re.findall(r'[\U0001F300-\U0001F9FF\u2600-\u27BF]', edited))
    if edit_emojis > orig_emojis + 2:
        rules.append({
            "type": "tone_preference",
            "direction": "more_emoji",
            "confidence": 6,
            "description": f"用户增加了 {edit_emojis - orig_emojis} 个 emoji，偏好更活泼的表达",
        })
    elif orig_emojis > edit_emojis + 2:
        rules.append({
            "type": "tone_preference",
            "direction": "less_emoji",
            "confidence": 6,
            "description": "用户减少了 emoji，偏好更严肃的表达",
        })

    # Rule 5: Personal voice injection
    first_person_patterns = ["我", "我的", "我觉得", "我认为", "我们"]
    orig_first_person = sum(original.count(p) for p in first_person_patterns)
    edit_first_person = sum(edited.count(p) for p in first_person_patterns)
    if edit_first_person > orig_first_person + 3:
        rules.append({
            "type": "voice_preference",
            "direction": "more_personal",
            "confidence": 7,
            "description": "用户增加了第一人称表达，偏好更多个人声音",
        })

    return rules


def update_playbook(rules: list[dict]):
    """Update the playbook with new rules, merging with existing ones."""
    existing_rules = []
    if PLAYBOOK_PATH.exists():
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        for line in content.split("\n"):
            if line.startswith("|") and "→" in line:
                parts = line.split("|")
                if len(parts) >= 5:
                    rule_type = parts[2].strip()
                    rule_action = parts[3].strip()
                    confidence_str = parts[4].strip()
                    try:
                        confidence = int(confidence_str)
                    except ValueError:
                        confidence = 5
                    existing_rules.append({
                        "type": rule_type,
                        "action": rule_action,
                        "confidence": confidence,
                        "description": parts[1].strip() if len(parts) > 1 else "",
                    })

    # Merge: if same type+action exists, average confidence
    for new_rule in rules:
        merged = False
        for existing in existing_rules:
            if existing["type"] == new_rule["type"] and existing.get("word", "") == new_rule.get("word", ""):
                existing["confidence"] = (existing["confidence"] + new_rule["confidence"]) // 2
                existing["confidence"] = min(existing["confidence"], 10)
                merged = True
                break
        if not merged:
            existing_rules.append(new_rule)

    # Sort by confidence
    existing_rules.sort(key=lambda r: r.get("confidence", 0), reverse=True)

    # Write back
    lines = ["# Writer Playbook", "", "用户个性化规则（自动学习生成）", "", "| 描述 | 类型 | 动作 | 置信度 |", "|------|------|------|--------|"]
    for rule in existing_rules:
        lines.append(f"| {rule.get('description', '')} | {rule['type']} | {rule.get('action', '')} | {rule.get('confidence', 5)} |")

    PLAYBOOK_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(existing_rules)


def save_lesson(original_path: str, edited_path: str, stats: dict, rules: list[dict]):
    """Save the lesson record."""
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    lesson_id = len(list(LESSONS_DIR.glob("lesson_*.yaml"))) + 1
    lesson_path = LESSONS_DIR / f"lesson_{lesson_id:03d}.yaml"

    lesson = {
        "id": lesson_id,
        "original": original_path,
        "edited": edited_path,
        "timestamp": None,  # Will be filled by agent
        "stats": stats,
        "rules_extracted": len(rules),
    }

    lesson_path.write_text(yaml.dump(lesson, allow_unicode=True, default_flow_style=False), encoding="utf-8")
    return lesson_path


def main():
    parser = argparse.ArgumentParser(description="Learn from user edits")
    parser.add_argument("original", nargs="?", help="Original AI-generated markdown file")
    parser.add_argument("edited", nargs="?", help="User-edited markdown file")
    parser.add_argument("--from-wechat", action="store_true", help="Sync from WeChat drafts")
    args = parser.parse_args()

    if args.from_wechat:
        print("从微信草稿箱同步功能需要配置微信 API，暂未实现。", file=sys.stderr)
        sys.exit(1)

    if not args.original or not args.edited:
        print("Usage: python3 learn_edits.py original.md edited.md", file=sys.stderr)
        sys.exit(1)

    orig_path = Path(args.original)
    edit_path = Path(args.edited)

    if not orig_path.exists():
        print(f"Error: original file not found: {args.original}", file=sys.stderr)
        sys.exit(1)
    if not edit_path.exists():
        print(f"Error: edited file not found: {args.edited}", file=sys.stderr)
        sys.exit(1)

    original_text = orig_path.read_text(encoding="utf-8")
    edited_text = edit_path.read_text(encoding="utf-8")

    # Compute diff stats
    stats = compute_diff_stats(original_text, edited_text)

    # Extract preference rules
    rules = extract_preference_rules(stats, original_text, edited_text)

    if not rules:
        print("未检测到明显的编辑偏好模式。")
        print(f"编辑率: {stats['edit_ratio']*100:.1f}%")
        print(f"字符变化: {stats['char_diff']:+d}")
        sys.exit(0)

    # Update playbook
    total_rules = update_playbook(rules)

    # Save lesson
    lesson_path = save_lesson(args.original, args.edited, stats, rules)

    print(f"学习完成！")
    print(f"  提取规则: {len(rules)} 条")
    print(f"  Playbook 规则总数: {total_rules} 条")
    print(f"  课程记录: {lesson_path}")
    print(f"\n提取的偏好规则:")
    for rule in rules:
        print(f"  - [{rule['type']}] {rule['description']} (置信度: {rule['confidence']}/10)")


if __name__ == "__main__":
    main()
