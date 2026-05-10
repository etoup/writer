#!/usr/bin/env python3
"""
Cache system for Writer — speeds up repeated operations.

Caches:
  - Hot topics (5 minute TTL)
  - SEO keywords (1 hour TTL)
  - Theme files (24 hour TTL)

Usage:
    python3 scripts/cache_manager.py status
    python3 scripts/cache_manager.py clear
    python3 scripts/cache_manager.py clear --key hotspots
"""

import hashlib
import json
import sys
import time
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

CACHE_TTL = {
    "hotspots": 300,        # 5 minutes
    "seo": 3600,            # 1 hour
    "theme": 86400,         # 24 hours
    "article": 0,           # never cache (user-specific)
}


def _cache_path(key: str) -> Path:
    """Get cache file path for a key."""
    return CACHE_DIR / f"{key}.json"


def get_cache(key: str) -> dict | None:
    """Get cached data if not expired."""
    path = _cache_path(key)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data.get("timestamp", 0) > CACHE_TTL.get(key, 3600):
            # Expired
            path.unlink(missing_ok=True)
            return None
        return data.get("data")
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def set_cache(key: str, data):
    """Cache data with timestamp."""
    path = _cache_path(key)
    cache_data = {
        "timestamp": time.time(),
        "data": data,
    }
    path.write_text(json.dumps(cache_data, ensure_ascii=False), encoding="utf-8")


def cache_key_for(*args) -> str:
    """Generate a cache key from arguments."""
    raw = "|".join(str(a) for a in args)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def clear_cache(key: str = None):
    """Clear cache (all or specific key)."""
    if key:
        path = _cache_path(key)
        if path.exists():
            path.unlink()
            print(f"Cleared cache: {key}")
        else:
            print(f"No cache found for: {key}")
    else:
        for path in CACHE_DIR.glob("*.json"):
            path.unlink()
        print(f"Cleared all cache ({len(list(CACHE_DIR.glob('*.json')))} files before clear)")


def cache_status():
    """Print cache status."""
    if not CACHE_DIR.exists():
        print("Cache directory does not exist.")
        return

    files = list(CACHE_DIR.glob("*.json"))
    if not files:
        print("Cache is empty.")
        return

    total_size = sum(f.stat().st_size for f in files)
    print(f"\nWriter Cache Status")
    print(f"{'='*40}")
    print(f"Location: {CACHE_DIR}")
    print(f"Entries: {len(files)}")
    print(f"Size: {total_size / 1024:.1f} KB")
    print()

    for f in sorted(files):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            age = time.time() - data.get("timestamp", 0)
            ttl = CACHE_TTL.get(f.stem, 3600)
            expired = age > ttl if ttl > 0 else False
            status = "EXPIRED" if expired else "VALID"
            print(f"  {f.name:20s} {status} (age: {age/60:.0f}m, TTL: {ttl/60:.0f}m)")
        except Exception:
            print(f"  {f.name:20s} CORRUPTED")

    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cache manager for Writer")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show cache status")
    p_clear = sub.add_parser("clear", help="Clear cache")
    p_clear.add_argument("--key", help="Specific cache key to clear")

    args = parser.parse_args()

    if args.command == "status":
        cache_status()
    elif args.command == "clear":
        clear_cache(args.key)


if __name__ == "__main__":
    main()
