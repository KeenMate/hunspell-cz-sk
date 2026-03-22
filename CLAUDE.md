# Hunspell Corrector — Czech FTS for PostgreSQL

## What is this project?

Czech hunspell dictionary corrector + PostgreSQL full-text search setup for insurance documents. Two main parts:

1. **Hunspell dictionary pipeline** — fixes and extends the Czech hunspell dictionary for better word recognition
2. **PostgreSQL FTS** — uses the corrected dictionary for full-text search over PDF insurance documents

## Project structure

### Hunspell dictionary tools
- `hunspell_fixer.py` — Main fixer: reverse morphology + consolidation of bare dict entries
- `tag_irregular_nouns.py` — Post-fixer: tags stem-changing nouns with R/J/Q/T/U flags
- `hunspell_checker.py` — PDF text checker against hunspell dictionary
- `analyze_irregular.py` — Analysis script for irregular noun patterns

### Database & FTS
- `debee.py` — PostgreSQL migration orchestrator (runs SQL scripts, tests)
- `debee.env` — Database connection config (localhost:5417, hunspell_test)
- `000_create_database.sql` — Database creation
- `001_create_basic_structure.sql` — Schemas (ext, helpers), extensions (unaccent, pg_trgm), version management
- `050_create_fts.sql` — Czech hunspell text search config (czech_hunspell → czech_simple fallback)
- `051_create_documents.sql` — Documents table with generated tsvector column
- `052_add_unaccent_tsv.sql` — Accent-insensitive tsvector column (immutable_unaccent wrapper + czech_simple_unaccent config)
- `060_create_sk_fts.sql` — Slovak hunspell text search config (slovak_hunspell → slovak_simple fallback)

### Distributable package (`package/`)
- `install_czech_fts.sql` — Czech dictionaries + configs + unaccent support (DBA-installable, no app logic)
- `install_slovak_fts.sql` — Slovak dictionaries + configs + unaccent support
- `tsearch_data/` — Dictionary files (cs_cz, sk_sk, stop words)
- `README.md` — Installation guide with usage examples (in Czech)

### Tools
- `pdf_extract.py` — Extract text from PDF files using PyMuPDF
- `insert_documents.py` — Insert extracted .txt files into documents table
- `search.py` — CLI full-text search with highlighted snippets (hunspell with fallback to unaccented)

### Tests
- `tests/test_documents/` — FTS test suite (debee runTests format)
  - `001_basic_fts.sql` — Basic queries: row count, tsvector populated, single-word searches
  - `002_complex_fts.sql` — AND/OR/NOT, phrase, proximity, ranking, plainto_tsquery, websearch_to_tsquery, ts_headline

## Quick start

```bash
make setup          # recreate DB + run migrations + insert documents
python search.py "pojistné plnění"        # search with diacritics (hunspell stemming)
python search.py pojistne plneni          # search without diacritics (unaccent fallback)
```

## Database commands (debee.py)

```bash
python debee.py -o fullService                    # recreate + restore + update
python debee.py -o updateDatabase -s 50 -n 52     # run specific migrations
python debee.py -o runTests --test-verbose         # run test suites
python debee.py -o execSql --sql-file some.sql     # run ad-hoc SQL file
```

## Search architecture

Two-tier full-text search:
1. **Primary (hunspell)**: `tsv` column — `to_tsvector('czech', body)` with Czech hunspell stemming. Requires proper diacritics.
2. **Fallback (unaccent)**: `tsv_unaccent` column — `to_tsvector('czech_simple_unaccent', immutable_unaccent(body))`. No stemming, but accent-insensitive.

The `search.py` script tries hunspell first; if no results, falls back to unaccented search.

### Why `immutable_unaccent`?

PostgreSQL's built-in `unaccent()` is declared as `STABLE`, not `IMMUTABLE`, because it depends on an external dictionary file that could theoretically change. However, `GENERATED ALWAYS AS` columns require all expressions to be `IMMUTABLE`. Since the unaccent rules never change at runtime, we create a thin wrapper `immutable_unaccent(text)` that calls `unaccent()` but is declared `IMMUTABLE`, allowing us to use it in the generated `tsv_unaccent` column.

## Windows notes

- Python stdout needs UTF-8 wrapping (`io.TextIOWrapper`) for Czech characters
- debee.py subprocess calls need `encoding="utf-8"` parameter
- psql connects via debee.env config, not direct PGPASSWORD env var
