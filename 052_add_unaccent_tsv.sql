set search_path = public, ext, helpers;

select start_version_update('3', 'Unaccented tsvector column', _component := 'hunspell_fts');

-- Immutable wrapper for unaccent (needed for generated columns)
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
    RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
AS $$ SELECT ext.unaccent($1); $$;

-- Simple text search config: unaccent filter + simple dictionary
CREATE TEXT SEARCH DICTIONARY czech_unaccent (
    Template = unaccent
);

CREATE TEXT SEARCH CONFIGURATION czech_simple_unaccent (COPY = simple);
ALTER TEXT SEARCH CONFIGURATION czech_simple_unaccent
    ALTER MAPPING FOR asciiword, word, hword, hword_part
    WITH czech_unaccent, simple;

-- Add unaccented tsvector column using immutable wrapper
ALTER TABLE documents
    ADD COLUMN tsv_unaccent tsvector GENERATED ALWAYS AS (
        to_tsvector('czech_simple_unaccent', immutable_unaccent(coalesce(body, '')))
    ) STORED;

CREATE INDEX idx_documents_tsv_unaccent ON documents USING gin(tsv_unaccent);

select stop_version_update('3', _component := 'hunspell_fts');
