# Vault rules (for the LLM)

You maintain this vault. The human rarely edits `wiki/` by hand.

## Agent playbook (call tools yourself)

This repo is built around **small CLIs**, not a bespoke server. **You are expected to run them** from the repository root when they help—using your terminal / run_command capability—instead of asking the user to copy-paste output.


| Tool | When to use it |
|------|----------------|
| `python3 tools/vault_cli.py search "…"` | Find lines mentioning a term (`--scope raw` / `wiki`). |
| `python3 tools/vault_cli.py search "…" --files-only` | One path per matching file (good for scripting). |
| `python3 tools/vault_cli.py list --scope raw` | Full inventory of `raw/**/*.md` paths. |
| `python3 tools/vault_cli.py index-gap` | **`raw/` files not yet mentioned** in `wiki/meta/source-index.md` (exit 1 if any gap). |
| `python3 tools/vault_cli.py stats` | Quick sense of vault size. |
| `python3 tools/vault_cli.py lint` | After you edit `wiki/` — fix broken `[[wikilinks]]`. |
| `python3 tools/raw_bundle.py` | Concatenate `raw/**/*.md` into **one stdout blob** (for pasting into `ollama_run -u` or a file). |
| `.venv/bin/python3 tools/ollama_web.py search` / `fetch` | Web snippets (needs venv + `ollama` + `OLLAMA_API_KEY` for cloud APIs). |
| `.venv/bin/python3 tools/ollama_run.py` | Local model chat (**stdout only**, does not write files); add `--web-tools` for search/fetch in a loop. |

**Make shortcuts (optional):** `make lint`, `make stats`, `make list-raw`, `make index-gap`, `make bundle` — see `Makefile`.

The **vault files are the durable state**; tools are **cheap, repeatable probes**. Prefer invoking a tool over inventing paths or “guessing” what’s in the tree.

### Runtime: cwd, `python` vs `python3`, and venv (avoid silent mistakes)

1. **Working directory** — Commands assume the **repository root** (the directory that contains `tools/`, `wiki/`, and `raw/`). From somewhere else you may get **`can't open file 'tools/vault_cli.py'`** or tools reading the **wrong tree** because `vault_cli.py` resolves paths relative to the repo root. **Always `cd` to that root first.**

2. **`python` vs `python3`** — Many systems only ship `python3`; `python` may be missing or a different version. If **`python` is not found**, rerun the same line with **`python3`**.

3. **`vault_cli.py` (stats / search / lint)** — **Stdlib only**; no venv required. Example: `python3 tools/vault_cli.py stats`.

4. **`ollama_run.py` and `ollama_web.py`** — Need the **`ollama`** package installed for the interpreter you use. **Wrong interpreter → `ModuleNotFoundError: No module named 'ollama'`** (or confusion if `python` points at an env that isn’t the one you `pip install`’d into).
   - **Recommended (no `activate` needed):**  
     `.venv/bin/python3 tools/ollama_run.py …`  
     `.venv/bin/python3 tools/ollama_web.py …`
   - **Alternative:** `source .venv/bin/activate` then `python3 tools/ollama_run.py …`
   - **One-time setup:** `python3 -m venv .venv && .venv/bin/pip install -r requirements-ollama.txt`

5. **Sanity checks before relying on output:**
   - `python3 tools/vault_cli.py stats` — must print `wiki:` / `raw:` counts (confirms cwd + Python).
   - `.venv/bin/python3 -c "import ollama"` — must exit **0** before using `ollama_run` / `ollama_web`.

6. **`OLLAMA_API_KEY`** — For `ollama_web` / `ollama_run --web-tools`, the variable must be set in the **same shell** as the command (see `Example.env`). Missing key produces an **explicit** error about authorization / Bearer, not empty success.

## Layout

- `raw/` — Source material only (clips, notes, exports). Do not delete without replacing provenance elsewhere.
- `wiki/` — Your compiled knowledge: concepts, source stubs, indices, Q&A outputs.
- `wiki/meta/` — `source-index.md` (one-line summaries per raw file), `manifest.json` (compile bookkeeping).
- `wiki/Outputs/` — Generated answers, slides, exports. Date or slug filenames.

## Conventions

- Wikilinks: `[[Concept Name]]` maps to `wiki/Concepts/<slug>.md` where slug is lowercase with hyphens.
- New raw file → add row to `wiki/meta/source-index.md`, create `wiki/Sources/<slug>.md` stub linking back to `raw/...`.
- After substantive edits, refresh `wiki/_index.md` hubs if navigation broke.
- Outputs must cite paths under `wiki/` or `raw/` they used.

## Compile checklist (agents)

1. **`python3 tools/vault_cli.py index-gap`** — If paths print, each is a `raw/` note **not referenced** in `wiki/meta/source-index.md` yet; add rows and wiki stubs when compiling.
2. **`python3 tools/vault_cli.py list --scope raw`** — See everything in `raw/`.
3. **Load context** — Read those files, or **`python3 tools/raw_bundle.py`** (optionally `> /tmp/raw-context.txt`) to build one blob for an LLM; **`ollama_run` does not read disk by itself**.
4. **Edit `wiki/`** (Sources, Concepts, `meta/source-index.md`, hubs) — you or the agent **write files**; do not expect `ollama_run` to do it.
5. **`python3 tools/vault_cli.py lint`** — Fix broken `[[wikilinks]]`.

## CLI reference (run from repo root)

```bash
python3 tools/vault_cli.py stats
python3 tools/vault_cli.py list --scope raw
python3 tools/vault_cli.py index-gap
python3 tools/vault_cli.py search "query words"
python3 tools/vault_cli.py search "query words" --scope raw --files-only
python3 tools/vault_cli.py lint
python3 tools/raw_bundle.py > /tmp/raw-bundle.txt
```

Optional — Ollama helpers (use **`.venv/bin/python3`** if you created `.venv` per Runtime §4):

```bash
.venv/bin/python3 tools/ollama_run.py -m llama3.2 -p prompts/ollama-compile-pass.md -u "Your concrete instruction."
.venv/bin/python3 tools/ollama_run.py --web-tools -m qwen3:4b -p prompts/ollama-qa.md -u "Research question with citations."
.venv/bin/python3 tools/ollama_web.py search "…"
.venv/bin/python3 tools/ollama_web.py fetch "https://…"
```

**Web APIs:** load `OLLAMA_API_KEY` (see `Example.env`). Docs: [Ollama web search](https://ollama.com/blog/web-search).

**Search `raw/` then Ollama:** `ollama_run` does not read the filesystem for you. See **`prompts/examples-raw-search-and-ollama.md`** for `vault_cli.py search` + `cat` into `-u`, or use an agent to read `raw/` and write `wiki/`.
