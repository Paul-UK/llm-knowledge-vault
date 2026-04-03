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
SOURCE_INDEX = WIKI / "meta" / "source-index.md"

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _md_files(base: Path, *, skip_obsidian: bool = True) -> list[Path]:
    if not base.is_dir():
        return []
    out: list[Path] = []
    for p in base.rglob("*.md"):
        if not p.is_file():
            continue
        if skip_obsidian and ".obsidian" in p.parts:
            continue
        out.append(p)
    return sorted(out, key=lambda x: x.as_posix())


def cmd_stats(_args: argparse.Namespace) -> int:
    w = _md_files(WIKI)
    r = _md_files(RAW)

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

    if args.files_only:
        seen: set[Path] = set()
        for base in bases:
            for p in _md_files(base):
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if needle in text.lower():
                    seen.add(p)
        paths = sorted(seen, key=lambda x: x.relative_to(ROOT).as_posix())
        if not paths:
            print("no hits", file=sys.stderr)
            return 1
        n = 0
        for p in paths:
            print(p.relative_to(ROOT).as_posix())
            n += 1
            if n >= args.max_files:
                print("(max files reached)", file=sys.stderr)
                break
        return 0

    hits = 0
    for base in bases:
        for p in _md_files(base):
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


def cmd_list(args: argparse.Namespace) -> int:
    bases: list[Path] = []
    if args.scope in ("all", "wiki"):
        bases.append(WIKI)
    if args.scope in ("all", "raw"):
        bases.append(RAW)
    paths: list[Path] = []
    for base in bases:
        paths.extend(_md_files(base))
    for p in sorted(paths, key=lambda x: x.relative_to(ROOT).as_posix()):
        print(p.relative_to(ROOT).as_posix())
    return 0


def cmd_index_gap(_args: argparse.Namespace) -> int:
    """List raw/**/*.md paths not mentioned in wiki/meta/source-index.md."""
    if not SOURCE_INDEX.is_file():
        print(f"missing {SOURCE_INDEX.relative_to(ROOT)}", file=sys.stderr)
        return 1
    try:
        blob = SOURCE_INDEX.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"read error: {e}", file=sys.stderr)
        return 1
    missing: list[str] = []
    for p in _md_files(RAW):
        rel = p.relative_to(ROOT).as_posix()
        if rel not in blob:
            missing.append(rel)
    for rel in sorted(missing):
        print(rel)
    return 1 if missing else 0


def resolve_wikilink(target: str) -> list[Path]:
    """Return candidate paths that would satisfy this wikilink target."""
    t = target.split("|")[0].strip()
    t = t.split("#")[0].strip()
    if not t:
        return []
    if "/" in t:
        return [WIKI / f"{t}.md"]
    return [WIKI / f"{t}.md", WIKI / "Concepts" / f"{t}.md"]


def cmd_lint(_args: argparse.Namespace) -> int:
    errors = 0
    for p in _md_files(WIKI):
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
        help="stop after this many matching lines (ignored with --files-only)",
    )
    s.add_argument(
        "--files-only",
        action="store_true",
        help="print each matching file path once (no line numbers)",
    )
    s.add_argument(
        "--max-files",
        type=int,
        default=500,
        help="with --files-only, max paths to print",
    )
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("list", help="list all .md paths under wiki/ and/or raw/")
    s.add_argument(
        "--scope",
        choices=("all", "wiki", "raw"),
        default="all",
        help="which tree to list",
    )
    s.set_defaults(func=cmd_list)

    s = sub.add_parser(
        "index-gap",
        help="raw .md files whose path does not appear in meta/source-index.md",
    )
    s.set_defaults(func=cmd_index_gap)

    s = sub.add_parser("lint", help="report broken wikilinks under wiki/")
    s.set_defaults(func=cmd_lint)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
