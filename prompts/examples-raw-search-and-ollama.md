# Examples: search `raw/`, then run Ollama with real context

`ollama_run.py` only sees what you put in the prompt and in `-u`. **Search finds files; you still attach paths or contents** so the model is grounded.

Run everything from the **repository root**.

---

## 1) Search `raw/` for keywords

```bash
python3 tools/vault_cli.py search "trading" --scope raw
python3 tools/vault_cli.py search "LLM" --scope raw
```

Output looks like `raw/some/path.md:42:matching line…` — use those paths in the next step.

**Unique files only (paths, one per line):**

```bash
python3 tools/vault_cli.py search "LLM" --scope raw --files-only
```

**Full inventory:**

```bash
python3 tools/vault_cli.py list --scope raw
```

**Find `raw/` notes missing from the source index:**

```bash
python3 tools/vault_cli.py index-gap
```

---

## 2) Compile one file you already know (small note)

Replace the path with yours, e.g. `raw/LLM trading/Financial trading via LLM.md`.

```bash
FILE='raw/LLM trading/Financial trading via LLM.md'
python3 tools/ollama_run.py -m gemma4:latest -p prompts/ollama-compile-pass.md -u "Compile this source into the wiki per AGENTS.md. Here is the full file.

Path: ${FILE}

$(cat "$FILE")
"
```

Large files: don’t paste more than your model’s context window; split or summarize first.

---

## 2b) Bundle all of `raw/` (or a glob) into one blob

Avoid manual `cat` for many files:

```bash
python3 tools/raw_bundle.py
python3 tools/raw_bundle.py 'raw/**/*.md'
python3 tools/raw_bundle.py > /tmp/raw-context.txt
```

Then pass the text into `-u` (or read from the file). Flags: `--max-files`, `--max-chars` if the bundle is too large.

**One-liner** (small vaults only):

```bash
python3 tools/ollama_run.py -m gemma4:latest -p prompts/ollama-compile-pass.md -u "$(echo 'Compile into wiki per AGENTS.md.' && python3 tools/raw_bundle.py)"
```

---

## 3) Search first, then paste (path-only is not enough)

`ollama_run` **cannot open** `raw/foo.md` from a path string alone. After search lists files, use **(2)**, **(2b)**, or **(4)**.

---

## 4) Agent-style (recommended for real wiki updates)

In Cursor chat, say something like:

> Search `raw/` for “trading”, read the matching `.md` files, then update `wiki/Sources/`, `wiki/Concepts/`, and `wiki/meta/source-index.md` per AGENTS.md. Run `python3 tools/vault_cli.py lint` after edits.

The agent has **file tools**; `ollama_run` alone does not.
