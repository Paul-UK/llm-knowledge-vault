You are maintaining a personal knowledge vault (Obsidian-friendly markdown).

**Repository layout**
- `raw/` — source clips and notes (read-only for you except adding new provenance).
- `wiki/` — compiled knowledge you may create and edit freely.
- Follow conventions in `AGENTS.md`.

**Task:** Ingest and compile.
1. Read any new or changed files under `raw/` (paths given by the user or from `git status`).
2. Update `wiki/meta/source-index.md` with a one-line summary per source.
3. Create or refresh `wiki/Sources/<slug>.md` stubs linking to the raw file.
4. Update or create `wiki/Concepts/*.md` for ideas mentioned; add backlinks.
5. Refresh `wiki/_index.md` hub links if needed.
6. Append compile records to `wiki/meta/manifest.json` (`entries` array: `{ "source": "raw/...", "wiki touched": ["..."] }`).

**Output format:** List files you changed, then stop. Use wikilinks `[[path/without/wiki/prefix]]` relative to `wiki/` root (e.g. `[[Concepts/foo]]`, `[[Sources/bar]]`).

**Tooling hint:** Run `python tools/vault_cli.py lint` after edits and fix broken `[[links]]`.
