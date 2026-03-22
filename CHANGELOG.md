# Changelog

## 2026-03-22 — Deployment verification test

- `package/test_deployment.sql` — 19-test suite for verifying dictionary deployment on target databases
  - Tests 1–6: Dictionary definitions — verifies template, DictFile, AffFile, StopWords for all 6 dictionaries
  - Tests 7–11: Czech FTS — config exists, hunspell stemming, query matching, fallback to simple, stop words
  - Tests 12–15: Unaccent — immutable_unaccent function, diacritics removal, config exists, accent-insensitive search
  - Tests 16–19: Slovak FTS — config exists, hunspell stemming, query matching, unaccent config

## 2026-03-11 — Standalone dictionary package

### Package (`package/`)
- Restructured as a clean DBA-installable package — dictionaries and configs only, no app-specific tables/indexes
- `install_czech_fts.sql` — Czech hunspell + simple fallback + unaccent support (immutable_unaccent, czech_simple_unaccent)
- `install_slovak_fts.sql` — Slovak hunspell + simple fallback + unaccent support (slovak_unaccent, slovak_simple_unaccent)
- Removed old migration scripts (050–052, 060) from package
- Updated README with "Použití ve vaší aplikaci" section showing example table/index creation for consumers

## 2026-03-04 — Full-text search & document pipeline

### Database
- `051_create_documents.sql` — Documents table (id, filename, body, generated tsv)
- `052_add_unaccent_tsv.sql` — Added `tsv_unaccent` column for accent-insensitive search
  - `immutable_unaccent()` wrapper function (required for generated columns)
  - `czech_simple_unaccent` text search config (unaccent filter + simple dictionary)

### Tools
- `pdf_extract.py` — PDF text extraction using PyMuPDF
- `insert_documents.py` — Inserts extracted .txt files into documents table via psycopg2
- `search.py` — CLI search tool with colored highlighted snippets
  - Hunspell search with stemming (primary)
  - Unaccent fallback for queries without diacritics

### Tests
- `tests/test_documents/001_basic_fts.sql` — 7 tests: row count, tsvector, single-word, domain-specific
- `tests/test_documents/002_complex_fts.sql` — 10 tests: AND/OR/NOT, phrase, proximity, ranking, plainto_tsquery, websearch_to_tsquery, ts_headline

### Fixes
- `debee.py` — Fixed UTF-8 encoding for subprocess output and stdout on Windows

### Documents indexed
- 3 Czech insurance PDFs (property, life, vehicle) — ~1.2M chars total

## 2025-03-04 — Czech hunspell dictionary & FTS config

### Database
- `000_create_database.sql` — Database creation
- `001_create_basic_structure.sql` — Schemas, extensions, version management
- `050_create_fts.sql` — Czech hunspell text search configuration

### Dictionary pipeline
- `hunspell_fixer.py` — Reverse morphology + consolidation
- `tag_irregular_nouns.py` — Stem-changing noun tagging (R/J/Q/T/U flags)
- `hunspell_checker.py` — PDF text checker
- Reduced bare words from 2,286 → 464
