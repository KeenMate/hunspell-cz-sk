set search_path = public, ext, helpers;

select start_version_update('2', 'Documents table', _component := 'hunspell_fts');

CREATE TABLE documents (
    id serial PRIMARY KEY,
    filename text NOT NULL,
    body text,
    tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('czech', coalesce(body, ''))
    ) STORED
);

CREATE INDEX idx_documents_tsv ON documents USING gin(tsv);

select stop_version_update('2', _component := 'hunspell_fts');
