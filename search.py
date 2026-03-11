"""Full-text search across documents with highlighted snippets."""

import io
import re
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import psycopg2

YELLOW = "\033[1;33m"
CYAN = "\033[1;36m"
GREEN = "\033[0;32m"
DIM = "\033[2m"
RESET = "\033[0m"

DB_PARAMS = {
    "host": "localhost",
    "port": 5416,
    "dbname": "hunspell_test",
    "user": "postgres",
    "password": "Password3000!!",
}

HEADLINE_OPTS = "StartSel=>>>, StopSel=<<<, MaxWords=25, MinWords=10, MaxFragments=3, FragmentDelimiter= ... "

# Primary: hunspell stemming (needs diacritics)
QUERY_HUNSPELL = f"""
SELECT filename,
       ts_rank(tsv, q) AS rank,
       ts_headline('czech', body, q, '{HEADLINE_OPTS}') AS snippet
FROM documents, websearch_to_tsquery('czech', %s) q
WHERE tsv @@ q
ORDER BY rank DESC
"""

# Fallback: unaccented simple search (no stemming, accent-insensitive)
QUERY_UNACCENT = f"""
SELECT filename,
       ts_rank(tsv_unaccent, q) AS rank,
       ts_headline('czech_simple_unaccent', ext.unaccent(body), q, '{HEADLINE_OPTS}') AS snippet
FROM documents, websearch_to_tsquery('czech_simple_unaccent', ext.unaccent(%s)) q
WHERE tsv_unaccent @@ q
ORDER BY rank DESC
"""


def colorize(snippet: str) -> str:
    return re.sub(r">>>(.+?)<<<", f"{YELLOW}\\1{RESET}", snippet)


def main():
    if len(sys.argv) < 2:
        print("Usage: python search.py <query>")
        print('Example: python search.py "pojistné podmínky smlouva"')
        print('         python search.py pojistne plneni   (without diacritics)')
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # Try hunspell first
    cur.execute(QUERY_HUNSPELL, (query,))
    rows = cur.fetchall()
    mode = "hunspell"

    # Fall back to unaccented search
    if not rows:
        cur.execute(QUERY_UNACCENT, (query,))
        rows = cur.fetchall()
        mode = "unaccent"

    if not rows:
        print(f'No results for "{query}"')
    else:
        label = f"{DIM}[{mode}]{RESET} " if mode == "unaccent" else ""
        print(f'Found {len(rows)} document(s) for "{query}" {label}\n')
        for filename, rank, snippet in rows:
            print(f"{CYAN}--- {filename} {GREEN}(rank: {rank:.4f}){CYAN} ---{RESET}")
            print(colorize(snippet))
            print()

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
