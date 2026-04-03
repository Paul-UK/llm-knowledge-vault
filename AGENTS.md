# Vault rules (for the LLM)

You maintain this vault. The human rarely edits `wiki/` by hand.

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

## CLI (run from repo root)

```bash
python tools/vault_cli.py stats
python tools/vault_cli.py search "query words"
python tools/vault_cli.py lint
```

Optional — local Ollama via Python (`pip install -r requirements-ollama.txt`):

```bash
python tools/ollama_run.py -m llama3.2 -p prompts/ollama-compile-pass.md -u "<task>"
```
