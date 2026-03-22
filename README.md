# Hunspell Corrector — Czech & Slovak FTS for PostgreSQL

Czech and Slovak hunspell dictionary corrector + PostgreSQL full-text search setup. Fixes and extends the open-source hunspell dictionaries so that PostgreSQL can properly stem inflected Czech/Slovak words back to their base forms.

## The problem

The standard Czech hunspell dictionary (from LibreOffice) contains ~190,000 "bare" entries — inflected word forms stored without affix flags. PostgreSQL cannot stem these back to their base form, so searching for "dům" (house) won't find documents containing "domu" (of a house).

This project fixes that with an automated reverse-morphology pipeline and custom affix rules for irregular nouns.

## What's included

### Hunspell dictionary pipeline

| Script | Purpose |
|--------|---------|
| `hunspell_fixer.py` | Reverse morphology + consolidation of bare dictionary entries |
| `tag_irregular_nouns.py` | Tags stem-changing nouns with custom affix flags (R/J/Q/T/U) |
| `hunspell_checker.py` | Checks PDF text coverage against the dictionary |
| `analyze_irregular.py` | Analysis script for irregular noun patterns |

**Pipeline:**
```bash
python hunspell_fixer.py --dict cs_cz.dict --affix cs_cz.affix -o cs_cz_fixed.dict -v
python tag_irregular_nouns.py --dict cs_cz_fixed.dict --affix cs_cz.affix -o cs_cz_final.dict -v
```

### PostgreSQL full-text search

SQL migrations that set up a two-tier FTS configuration:

1. **Primary (hunspell)** — `to_tsvector('czech', body)` with Czech hunspell stemming. Requires proper diacritics.
2. **Fallback (unaccent)** — `to_tsvector('czech_simple_unaccent', immutable_unaccent(body))`. No stemming, but accent-insensitive.

| Migration | What it does |
|-----------|-------------|
| `000_create_database.sql` | Database creation |
| `001_create_basic_structure.sql` | Schemas (ext, helpers), extensions (unaccent, pg_trgm), version management |
| `050_create_fts.sql` | Czech hunspell text search config (czech_hunspell → czech_simple fallback) |
| `051_create_documents.sql` | Documents table with generated tsvector column |
| `052_add_unaccent_tsv.sql` | Accent-insensitive tsvector column (immutable_unaccent wrapper) |
| `060_create_sk_fts.sql` | Slovak hunspell text search config |

### Distributable package (`package/`)

A standalone, DBA-installable package containing only the dictionaries and FTS configurations — no application logic. Copy dictionary files to PostgreSQL's `tsearch_data/` directory and run the install scripts. See [`package/README.md`](package/README.md) for detailed instructions.

### Tools

| Script | Purpose |
|--------|---------|
| `pdf_extract.py` | Extract text from PDF files (PyMuPDF) |
| `insert_documents.py` | Insert extracted `.txt` files into the documents table |
| `search.py` | CLI full-text search with colored highlighted snippets |

### Database orchestration (`debee.py`)

Migration runner that handles database creation, schema updates, and test execution:

```bash
python debee.py -o fullService                    # recreate + restore + update
python debee.py -o updateDatabase -s 50 -n 52     # run specific migrations
python debee.py -o runTests --test-verbose         # run test suites
python debee.py -o execSql --sql-file some.sql     # run ad-hoc SQL file
```

## Quick start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ with `unaccent` and `pg_trgm` extensions
- PyMuPDF (`pip install pymupdf`) for PDF extraction
- psycopg2 (`pip install psycopg2-binary`) for database operations

### Setup

```bash
# Configure database connection in debee.env, then:
make setup          # recreate DB + run migrations + insert documents

# Search with diacritics (hunspell stemming):
python search.py "pojistné plnění"

# Search without diacritics (unaccent fallback):
python search.py pojistne plneni
```

## Dictionary corrections — results

### Czech

| Metric | Before | After |
|--------|--------|-------|
| Dictionary entries | 524,209 | 387,959 |
| Expanded word forms | — | 1,060,998 |
| Remaining bare entries | ~190,000+ | 51,632 |

**Custom affix flags added:**

| Flag | Pattern | Example | Description |
|------|---------|---------|-------------|
| R | ů → o | dům → domu | Vowel alternation |
| J | fleeting -e- (masc.) | příjem → příjmu | Consonant cluster restoration |
| Q | fleeting -e- (fem.) | povodeň → povodně | Feminine variant |
| T | k → c (animate) | pojistník → pojistníci | Palatalization in nom. pl. |
| U | k → c (inanimate) | nárok → nárocích | Palatalization in loc. pl. |

### Slovak

| Metric | Before | After |
|--------|--------|-------|
| Dictionary entries | 160,684 | 155,076 |
| Expanded word forms | 2,816,146 | 2,816,739 |
| Remaining bare entries | 68,743 | 64,024 |

Slovak dictionary needed fewer fixes — its original affix system (3,438 rules in 28 flags) is much richer than the Czech one.

## Tests

FTS test suite in `tests/test_documents/`:

- `001_basic_fts.sql` — Row count, tsvector populated, single-word searches
- `002_complex_fts.sql` — AND/OR/NOT, phrase, proximity, ranking, plainto/websearch_to_tsquery, ts_headline

Run with:
```bash
python debee.py -o runTests --test-verbose
```

### Deployment verification

`package/test_deployment.sql` — 19 tests to verify dictionaries are properly installed on a target database (dictionary definitions, stemming, fallback, stop words, unaccent). Run directly with psql after deploying the package.

## Why `immutable_unaccent`?

PostgreSQL's built-in `unaccent()` is declared `STABLE`, but `GENERATED ALWAYS AS` columns require `IMMUTABLE` expressions. Since unaccent rules never change at runtime, we wrap it in an `IMMUTABLE` function to make generated tsvector columns work.

## License

Dictionary files are based on the Czech and Slovak hunspell dictionaries from the LibreOffice project.
