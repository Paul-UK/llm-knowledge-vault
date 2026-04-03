#!/usr/bin/env python3
"""Call the local Ollama HTTP API from Python (official `ollama` package).

Install: pip install -r requirements-ollama.txt
Requires: `ollama serve` running (default http://127.0.0.1:11434).

Example:
  python3 tools/ollama_run.py -m llama3.2 \\
    -p prompts/ollama-compile-pass.md \\
    -u "Compile any new files under raw/samples/ into the wiki per AGENTS.md."
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _message_content(chunk: object) -> str:
    """Support ChatResponse objects and dict-shaped responses."""
    msg = getattr(chunk, "message", None)
    if msg is not None:
        return getattr(msg, "content", None) or ""
    if isinstance(chunk, dict):
        inner = chunk.get("message") or {}
        return inner.get("content") or ""
    return ""


def main() -> int:
    try:
        import ollama
    except ImportError:
        print(
            "Missing package `ollama`. Install with:\n"
            "  pip install -r requirements-ollama.txt",
            file=sys.stderr,
        )
        return 2

    ap = argparse.ArgumentParser(description="Chat with local Ollama (Python client)")
    ap.add_argument(
        "-m",
        "--model",
        default=os.environ.get("OLLAMA_MODEL", "llama3.2"),
        help="Model name (default: $OLLAMA_MODEL or llama3.2)",
    )
    ap.add_argument(
        "-p",
        "--prompt-file",
        type=Path,
        help="Markdown file whose full text becomes the system message",
    )
    ap.add_argument(
        "-u",
        "--user",
        default="",
        help="User message (instructions / question)",
    )
    ap.add_argument(
        "--stream",
        action="store_true",
        help="Stream tokens to stdout",
    )
    args = ap.parse_args()

    messages: list[dict] = []
    if args.prompt_file:
        path = args.prompt_file if args.prompt_file.is_absolute() else ROOT / args.prompt_file
        if not path.is_file():
            print(f"not found: {path}", file=sys.stderr)
            return 1
        messages.append(
            {"role": "system", "content": path.read_text(encoding="utf-8")}
        )

    user = (args.user or "").strip()
    if not user:
        user = "Reply with a short acknowledgment; the user will send real prompts next."
    messages.append({"role": "user", "content": user})

    kwargs = {"model": args.model, "messages": messages}
    try:
        if args.stream:
            stream = ollama.chat(stream=True, **kwargs)
            for part in stream:
                print(_message_content(part), end="", flush=True)
            print()
            return 0

        resp = ollama.chat(**kwargs)
        print(_message_content(resp))
        return 0
    except Exception as e:
        print(
            f"Ollama request failed: {e}\n"
            "Is the daemon running? Try: ollama serve  (or start the Ollama app)",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
