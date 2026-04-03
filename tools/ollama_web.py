#!/usr/bin/env python3
"""Ollama cloud web search / fetch (requires OLLAMA_API_KEY).

See: https://ollama.com/blog/web-search

These calls hit Ollama's API at ollama.com, not your local `ollama serve`.
Use output to seed raw/ clips or to paste into a compile prompt.
"""

from __future__ import annotations

import argparse
import sys


def _require_ollama():
    try:
        import ollama
    except ImportError:
        print(
            "Install: pip install -r requirements-ollama.txt",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
    return ollama


def cmd_search(args: argparse.Namespace) -> int:
    ollama = _require_ollama()
    try:
        resp = ollama.web_search(args.query, max_results=args.max_results)
    except ValueError as e:
        print(
            f"{e}\n"
            "Create an API key in your Ollama account and export:\n"
            "  export OLLAMA_API_KEY=...\n"
            "Docs: https://ollama.com/blog/web-search",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"web_search failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(resp.model_dump_json(indent=2))
        return 0

    for i, r in enumerate(resp.results, 1):
        title = r.title or "(no title)"
        url = r.url or ""
        body = (r.content or "").strip().replace("\n", " ")
        if len(body) > 500:
            body = body[:500] + "…"
        print(f"### {i}. {title}\n{url}\n\n{body}\n")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    ollama = _require_ollama()
    try:
        resp = ollama.web_fetch(args.url)
    except ValueError as e:
        print(
            f"{e}\n"
            "Set OLLAMA_API_KEY (Bearer) per https://ollama.com/blog/web-search",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"web_fetch failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(resp.model_dump_json(indent=2))
        return 0

    title = resp.title or "(no title)"
    print(f"# {title}\n")
    print(resp.content or "")
    if resp.links:
        print("\n## Links\n")
        for link in resp.links:
            print(f"- {link}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Ollama web_search / web_fetch CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="Search the web via Ollama API")
    s.add_argument("query", help="search query")
    s.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="max hits (default 5)",
    )
    s.add_argument("--json", action="store_true", help="print raw JSON")
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("fetch", help="Fetch one URL via Ollama API")
    s.add_argument("url", help="https://...")
    s.add_argument("--json", action="store_true", help="print raw JSON")
    s.set_defaults(func=cmd_fetch)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
