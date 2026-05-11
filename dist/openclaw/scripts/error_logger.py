#!/usr/bin/env python3
"""
error_logger.py — Track and analyze errors in Writer scripts.

Provides centralized error logging and analysis for all Writer tools.
Logs errors to .writer_errors.log with structured format.

Usage:
    python3 scripts/error_logger.py --log "Error message" --script "data_report.py"
    python3 scripts/error_logger.py --show
    python3 scripts/error_logger.py --show --json
    python3 scripts/error_logger.py --clear
    python3 scripts/error_logger.py --stats
"""

import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path


def get_log_path(skill_dir):
    return Path(skill_dir) / ".writer_errors.log"


def load_errors(skill_dir):
    log_path = get_log_path(skill_dir)
    if not log_path.exists():
        return []

    errors = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    errors.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return errors


def save_error(skill_dir, error_data):
    log_path = get_log_path(skill_dir)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_data, ensure_ascii=False) + "\n")


def log_error(skill_dir, message, script_name=None, error_type=None, traceback_str=None):
    error_data = {
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "script": script_name or "unknown",
        "type": error_type or "unknown",
        "traceback": traceback_str or "",
    }
    save_error(skill_dir, error_data)
    return error_data


def show_errors(skill_dir, limit=20):
    errors = load_errors(skill_dir)
    if not errors:
        print("No errors recorded.")
        return

    errors = errors[-limit:]
    errors.reverse()

    print(f"Recent Errors (showing {len(errors)} of {len(load_errors(skill_dir))} total):\n")
    for i, err in enumerate(errors, 1):
        print(f"[{i}] {err['timestamp']}")
        print(f"    Script: {err['script']}")
        print(f"    Type: {err['type']}")
        print(f"    Message: {err['message']}")
        if err.get("traceback"):
            print(f"    Traceback: {err['traceback'][:200]}...")
        print()


def show_stats(skill_dir):
    errors = load_errors(skill_dir)
    if not errors:
        print("No errors recorded.")
        return

    total = len(errors)
    script_counts = {}
    type_counts = {}
    recent_errors = 0

    now = datetime.now()
    for err in errors:
        try:
            ts = datetime.fromisoformat(err["timestamp"])
            if (now - ts).days <= 7:
                recent_errors += 1
        except Exception:
            pass

        script = err.get("script", "unknown")
        script_counts[script] = script_counts.get(script, 0) + 1

        etype = err.get("type", "unknown")
        type_counts[etype] = type_counts.get(etype, 0) + 1

    print("Error Statistics:")
    print(f"  Total errors: {total}")
    print(f"  Errors (last 7 days): {recent_errors}")
    print(f"\nBy Script:")
    for script, count in sorted(script_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {script}: {count}")
    print(f"\nBy Type:")
    for etype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {etype}: {count}")


def clear_errors(skill_dir):
    log_path = get_log_path(skill_dir)
    if log_path.exists():
        log_path.unlink()
        print("Error log cleared.")
    else:
        print("No error log found.")


def main():
    parser = argparse.ArgumentParser(description="Writer error logger")
    parser.add_argument("--log", type=str, default=None, help="Log an error message")
    parser.add_argument("--script", type=str, default=None, help="Script name for logging")
    parser.add_argument("--type", type=str, default=None, help="Error type")
    parser.add_argument("--traceback", type=str, default=None, help="Traceback string")
    parser.add_argument("--show", action="store_true", help="Show recent errors")
    parser.add_argument("--stats", action="store_true", help="Show error statistics")
    parser.add_argument("--clear", action="store_true", help="Clear error log")
    parser.add_argument("--limit", type=int, default=20, help="Limit for --show")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent

    if args.log:
        result = log_error(skill_dir, args.log, args.script, args.type, args.traceback)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Error logged: {args.log}")
        return

    if args.show:
        if args.json:
            errors = load_errors(skill_dir)[-args.limit:]
            print(json.dumps(errors, ensure_ascii=False, indent=2))
        else:
            show_errors(skill_dir, args.limit)
        return

    if args.stats:
        show_stats(skill_dir)
        return

    if args.clear:
        clear_errors(skill_dir)
        return

    parser.print_help()


class ErrorLogger:
    """Context manager for easy error logging in scripts."""

    def __init__(self, script_name):
        self.script_name = script_name
        self.skill_dir = Path(__file__).parent.parent

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            log_error(
                self.skill_dir,
                str(exc_val),
                self.script_name,
                exc_type.__name__,
                "".join(traceback.format_tb(exc_tb))[-500:],
            )
        return False


if __name__ == "__main__":
    main()
