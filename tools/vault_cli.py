#!/usr/bin/env python3
"""Small CLI for vault search / stats / wikilink lint. No third-party deps."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def md_files(base: Path) -> list[Path]:
    if not base.is_dir():
        return []
    return sorted(p for p in base.rglob("*.md") if p.is_file())


def cmd_stats(_args: argparse.Namespace) -> int:
    w = md_files(WIKI)
    r = md_files(RAW)
    def words(paths: list[Path]) -> int:
        n = 0
        for p in paths:
            try:
                n += len(p.read_text(encoding="utf-8", errors="replace").split())
            except OSError:
                pass
        return n

    print(f"wiki: {len(w)} markdown files, ~{words(w)} words")
    print(f"raw:  {len(r)} markdown files, ~{words(r)} words")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    needle = args.query.lower()
    scope = args.scope
    bases: list[Path] = []
    if scope in ("all", "wiki"):
        bases.append(WIKI)
    if scope in ("all", "raw"):
        bases.append(RAW)
    hits = 0
    for base in bases:
        for p in md_files(base):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if needle in line.lower():
                    rel = p.relative_to(ROOT)
                    print(f"{rel}:{i}:{line.strip()[:200]}")
                    hits += 1
                    if hits >= args.max_hits:
                        print("(max hits reached)", file=sys.stderr)
                        return 0
    if hits == 0:
        print("no hits", file=sys.stderr)
        return 1
    return 0


def resolve_wikilink(target: str) -> list[Path]:
    """Return candidate paths that would satisfy this wikilink target."""
    t = target.split("|")[0].strip()
    t = t.split("#")[0].strip()
    if not t:
        return []
    if "/" in t:
        return [WIKI / f"{t}.md"]
    # Try direct under wiki, then Concepts/
    return [WIKI / f"{t}.md", WIKI / "Concepts" / f"{t}.md"]


def cmd_lint(_args: argparse.Namespace) -> int:
    errors = 0
    for p in md_files(WIKI):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in WIKILINK_RE.finditer(text):
            inner = m.group(1)
            display = inner.split("|")[0].split("#")[0].strip()
            if display.lower().startswith("http"):
                continue
            candidates = resolve_wikilink(inner)
            if any(c.is_file() for c in candidates):
                continue
            rel = p.relative_to(ROOT)
            errors += 1
            print(f"broken wikilink: {rel}: [[{inner}]]")
    return 1 if errors else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="LLM knowledge vault helpers")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("stats", help="file and word counts")
    s.set_defaults(func=cmd_stats)

    s = sub.add_parser("search", help="grep bodies of markdown")
    s.add_argument("query", help="substring to match (case-insensitive)")
    s.add_argument(
        "--scope",
        choices=("all", "wiki", "raw"),
        default="all",
        help="where to search",
    )
    s.add_argument(
        "--max-hits",
        type=int,
        default=200,
        help="stop after this many matching lines",
    )
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("lint", help="report broken wikilinks under wiki/")
    s.set_defaults(func=cmd_lint)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
