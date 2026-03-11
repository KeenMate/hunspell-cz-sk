"""Insert extracted PDF texts into the documents table."""

import sys
from pathlib import Path

import psycopg2

DOCS_DIR = Path(__file__).parent / "docs" / "cz"

DB_PARAMS = {
    "host": "localhost",
    "port": 5416,
    "dbname": "hunspell_test",
    "user": "postgres",
    "password": "Password3000!!",
}


def main():
    if not DOCS_DIR.exists():
        print(f"ERROR: docs directory not found: {DOCS_DIR}")
        sys.exit(1)

    txt_files = sorted(DOCS_DIR.glob("*.txt"))
    if not txt_files:
        print(f"No .txt files found in {DOCS_DIR}")
        sys.exit(1)

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for txt_path in txt_files:
        body = txt_path.read_text(encoding="utf-8")
        pdf_name = txt_path.with_suffix(".pdf").name

        cur.execute(
            "INSERT INTO documents (filename, body) VALUES (%s, %s) "
            "ON CONFLICT DO NOTHING RETURNING id",
            (pdf_name, body),
        )
        row = cur.fetchone()
        if row:
            print(f"OK    {pdf_name} -> id={row[0]}  ({len(body)} chars)")
        else:
            print(f"SKIP  {pdf_name} (already exists)")

    conn.commit()
    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
