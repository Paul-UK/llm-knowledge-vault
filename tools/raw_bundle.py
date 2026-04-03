#!/usr/bin/env python3
"""Concatenate markdown under raw/ into one text block for LLM context (stdout).

Skips **/.obsidian/**. Use with ollama_run -u or redirect to a file.
No third-party deps."""

from __future__ import annotations

import argparse
import glob as glob_mod
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _should_skip(path: Path) -> bool:
    return ".obsidian" in path.parts


def _collect_files(patterns: list[str]) -> list[Path]:
    files: set[Path] = set()
    for pat in patterns:
        p = Path(pat)
        if not p.is_absolute():
            p = ROOT / pat
        if p.is_file() and p.suffix.lower() == ".md":
            if not _should_skip(p):
                files.add(p.resolve())
            continue
        # Glob from repo root (supports **)
        gpat = str(ROOT / pat.lstrip("/"))
        for s in glob_mod.glob(gpat, recursive=True):
            path = Path(s)
            if not path.is_file() or path.suffix.lower() != ".md":
                continue
            if _should_skip(path):
                continue
            files.add(path.resolve())
    return sorted(files, key=lambda x: x.as_posix())


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Bundle .md files into one stdout blob for LLM prompts."
    )
    ap.add_argument(
        "paths",
        nargs="*",
        help="Optional glob(s) or file paths (default: raw/**/*.md)",
    )
    ap.add_argument(
        "--max-files",
        type=int,
        default=200,
        help="Stop after N files (default 200)",
    )
    ap.add_argument(
        "--max-chars",
        type=int,
        default=200_000,
        help="Stop when total output would exceed N characters (default 200000)",
    )
    args = ap.parse_args()
    patterns = args.paths if args.paths else ["raw/**/*.md"]

    files = _collect_files(patterns)
    if not files:
        print("raw_bundle: no matching .md files", file=sys.stderr)
        return 1
    if len(files) > args.max_files:
        print(
            f"raw_bundle: {len(files)} files match; limit is --max-files={args.max_files}",
            file=sys.stderr,
        )
        return 1

    out: list[str] = []
    total = 0
    for fp in files:
        rel = fp.relative_to(ROOT).as_posix()
        header = f"\n--- path: {rel} ---\n"
        try:
            body = fp.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"raw_bundle: skip {rel}: {e}", file=sys.stderr)
            continue
        chunk = header + body
        if total + len(chunk) > args.max_chars:
            print(
                f"raw_bundle: would exceed --max-chars={args.max_chars} at {rel}",
                file=sys.stderr,
            )
            return 1
        out.append(chunk)
        total += len(chunk)

    if not out:
        return 1
    sys.stdout.write("".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
