# LLM knowledge vault — common agent commands (run from repo root)
.PHONY: help lint stats list-raw list-wiki list-all index-gap bundle

help:
	@echo "Targets: lint stats list-raw list-wiki list-all index-gap bundle"
	@echo "  lint       - broken [[wikilinks]] in wiki/"
	@echo "  stats      - file/word counts"
	@echo "  list-raw   - all raw/**/*.md paths"
	@echo "  list-wiki  - all wiki/**/*.md paths"
	@echo "  list-all   - raw + wiki paths"
	@echo "  index-gap  - raw files not mentioned in meta/source-index.md (exit 1 if any)"
	@echo "  bundle     - concatenate raw/**/*.md to stdout (for LLM context)"

lint:
	python3 tools/vault_cli.py lint

stats:
	python3 tools/vault_cli.py stats

list-raw:
	python3 tools/vault_cli.py list --scope raw

list-wiki:
	python3 tools/vault_cli.py list --scope wiki

list-all:
	python3 tools/vault_cli.py list --scope all

index-gap:
	python3 tools/vault_cli.py index-gap

bundle:
	python3 tools/raw_bundle.py
