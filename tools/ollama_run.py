#!/usr/bin/env python3
"""Call the local Ollama HTTP API from Python (official `ollama` package).

Install: pip install -r requirements-ollama.txt
Requires: `ollama serve` running (default http://127.0.0.1:11434).

Example:
  python3 tools/ollama_run.py -m llama3.2 \\
    -p prompts/ollama-compile-pass.md \\
    -u "Compile any new files under raw/samples/ into the wiki per AGENTS.md."

Web tools (Ollama cloud search/fetch; needs OLLAMA_API_KEY):
  https://ollama.com/blog/web-search
  python3 tools/ollama_run.py --web-tools -m qwen3:4b \\
    -p prompts/ollama-qa.md -u "What changed in Ollama's engine in 2025?"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]

_WEB_TOOLS_HINT = (
    "\n\nYou may call **web_search** and **web_fetch** when fresh sources or a "
    "specific URL would help. Prefer citing titles and URLs. For vault work, "
    "propose concrete markdown paths under raw/ or wiki/ when relevant."
)


def _message_content(chunk: object) -> str:
    """Support ChatResponse objects and dict-shaped responses."""
    msg = getattr(chunk, "message", None)
    if msg is not None:
        return getattr(msg, "content", None) or ""
    if isinstance(chunk, dict):
        inner = chunk.get("message") or {}
        return inner.get("content") or ""
    return ""


def _tool_result_text(result: object, max_chars: int) -> str:
    if hasattr(result, "model_dump_json"):
        text = result.model_dump_json()
    else:
        text = str(result)
    if len(text) > max_chars:
        return text[:max_chars] + "\n…[truncated]"
    return text


def _run_chat_with_web_tools(
    *,
    model: str,
    messages: list[Any],
    max_rounds: int,
    think: bool,
    verbose_tools: bool,
) -> int:
    import ollama

    available: dict[str, Any] = {
        "web_search": ollama.web_search,
        "web_fetch": ollama.web_fetch,
    }
    max_tool_chars = int(os.environ.get("OLLAMA_VAULT_TOOL_CHARS", "12000"))

    for _ in range(max_rounds):
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "tools": [ollama.web_search, ollama.web_fetch],
        }
        if think:
            kwargs["think"] = True
        try:
            response = ollama.chat(**kwargs)
        except ValueError as e:
            print(
                f"{e}\n"
                "Export OLLAMA_API_KEY from your Ollama account.\n"
                "https://ollama.com/blog/web-search",
                file=sys.stderr,
            )
            return 1
        except Exception as e:
            print(f"Ollama chat failed: {e}", file=sys.stderr)
            return 1

        msg = response.message
        if getattr(msg, "thinking", None):
            print(msg.thinking, file=sys.stderr)
            print(file=sys.stderr)
        if msg.content:
            print(msg.content, end="\n", flush=True)
        messages.append(msg)
        tc = msg.tool_calls
        if not tc:
            return 0
        for tool_call in tc:
            name = tool_call.function.name
            raw_args: Mapping[str, Any] = tool_call.function.arguments
            args = dict(raw_args)
            fn = available.get(name)
            if verbose_tools:
                print(f"[tool {name} {args}]", file=sys.stderr, flush=True)
            if fn is None:
                out_text = f"unknown tool: {name}"
            else:
                try:
                    out = fn(**args)
                    out_text = _tool_result_text(out, max_tool_chars)
                except Exception as exc:
                    out_text = f"error: {exc}"
            messages.append(
                {
                    "role": "tool",
                    "content": out_text,
                    "tool_name": name,
                }
            )
        print(file=sys.stderr)

    print(f"(stopped after {max_rounds} tool rounds)", file=sys.stderr)
    return 1


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
    ap.add_argument(
        "--web-tools",
        action="store_true",
        help="Enable Ollama web_search + web_fetch in a tool loop (needs OLLAMA_API_KEY)",
    )
    ap.add_argument(
        "--max-tool-rounds",
        type=int,
        default=16,
        help="With --web-tools, max assistant+tool iterations (default 16)",
    )
    ap.add_argument(
        "--think",
        action="store_true",
        help="With --web-tools, pass think=True for models that support it",
    )
    ap.add_argument(
        "-v",
        "--verbose-tools",
        action="store_true",
        help="With --web-tools, log each tool call to stderr",
    )
    args = ap.parse_args()

    if args.stream and args.web_tools:
        print("Cannot combine --stream with --web-tools.", file=sys.stderr)
        return 2

    messages: list[Any] = []
    if args.prompt_file:
        path = args.prompt_file if args.prompt_file.is_absolute() else ROOT / args.prompt_file
        if not path.is_file():
            print(f"not found: {path}", file=sys.stderr)
            return 1
        sys_body = path.read_text(encoding="utf-8")
        if args.web_tools:
            sys_body = sys_body + _WEB_TOOLS_HINT
        messages.append({"role": "system", "content": sys_body})
    elif args.web_tools:
        messages.append(
            {
                "role": "system",
                "content": "You are a helpful assistant." + _WEB_TOOLS_HINT,
            }
        )

    user = (args.user or "").strip()
    if not user:
        user = "Reply with a short acknowledgment; the user will send real prompts next."
    messages.append({"role": "user", "content": user})

    if args.web_tools:
        return _run_chat_with_web_tools(
            model=args.model,
            messages=messages,
            max_rounds=max(1, args.max_tool_rounds),
            think=args.think,
            verbose_tools=args.verbose_tools,
        )

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
