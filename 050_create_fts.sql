set search_path = public, ext, helpers;

select start_version_update('1', 'Czech FTS Setup', _component := 'hunspell_fts');

-- ---------------------------------------------------------------------------
-- Czech hunspell dictionary (uses files from tsearch_data/)
-- ---------------------------------------------------------------------------

CREATE TEXT SEARCH DICTIONARY czech_hunspell (
    Template = ispell,
    DictFile = cs_cz,
    AffFile = cs_cz,
    StopWords = czech
);

-- Simple fallback for unknown words
CREATE TEXT SEARCH DICTIONARY czech_simple (
    Template = simple,
    StopWords = czech
);

-- Text search configuration chaining hunspell → simple
CREATE TEXT SEARCH CONFIGURATION czech (COPY = simple);
ALTER TEXT SEARCH CONFIGURATION czech
    ALTER MAPPING FOR asciiword, word, hword, hword_part
    WITH czech_hunspell, czech_simple;

-- ---------------------------------------------------------------------------
-- Test table with generated tsvector column
-- ---------------------------------------------------------------------------

CREATE TABLE test_documents (
    id serial PRIMARY KEY,
    title text NOT NULL,
    body text,
    tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('czech', coalesce(title, '') || ' ' || coalesce(body, ''))
    ) STORED
);

CREATE INDEX idx_test_documents_tsv ON test_documents USING gin(tsv);

-- ---------------------------------------------------------------------------
-- Sample data for verification
-- ---------------------------------------------------------------------------

INSERT INTO test_documents (title, body) VALUES
    ('Pojištění domu', 'Pojistník uzavřel smlouvu na pojištění rodinného domu a domácnosti.'),
    ('Příjem a výdaje', 'Příjmy z pronájmu bytů byly vyšší než nájemné za kancelářské prostory.'),
    ('Zákrok lékaře', 'Lékař provedl chirurgický zákrok v nemocnici.');

-- ---------------------------------------------------------------------------
-- Verification queries
-- ---------------------------------------------------------------------------

SELECT id, title, ts_rank(tsv, q) AS rank
FROM test_documents, to_tsquery('czech', 'dům') q
WHERE tsv @@ q;

SELECT id, title, ts_rank(tsv, q) AS rank
FROM test_documents, to_tsquery('czech', 'pojistník') q
WHERE tsv @@ q;

SELECT id, title, ts_rank(tsv, q) AS rank
FROM test_documents, to_tsquery('czech', 'příjem') q
WHERE tsv @@ q;

select stop_version_update('1', _component := 'hunspell_fts');
