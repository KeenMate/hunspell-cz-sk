-- ============================================================================
-- Slovak FTS dictionaries for PostgreSQL
-- ============================================================================
-- Prerequisites:
--   1. Copy sk_sk.dict, sk_sk.affix, slovak.stop to PostgreSQL's tsearch_data/
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Slovak hunspell dictionary (uses files from tsearch_data/)
-- ---------------------------------------------------------------------------

CREATE TEXT SEARCH DICTIONARY slovak_hunspell (
    Template = ispell,
    DictFile = sk_sk,
    AffFile = sk_sk,
    StopWords = slovak
);

-- Simple fallback for unknown words
CREATE TEXT SEARCH DICTIONARY slovak_simple (
    Template = simple,
    StopWords = slovak
);

-- Text search configuration chaining hunspell → simple
CREATE TEXT SEARCH CONFIGURATION slovak (COPY = simple);
ALTER TEXT SEARCH CONFIGURATION slovak
    ALTER MAPPING FOR asciiword, word, hword, hword_part
    WITH slovak_hunspell, slovak_simple;

-- ---------------------------------------------------------------------------
-- Unaccent support (for accent-insensitive search)
-- ---------------------------------------------------------------------------

-- Reuses immutable_unaccent() from install_czech_fts.sql if already installed.
-- If installing Slovak standalone, uncomment the following:
--
-- CREATE OR REPLACE FUNCTION immutable_unaccent(text)
--     RETURNS text
--     LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
-- AS $$ SELECT unaccent($1); $$;

CREATE TEXT SEARCH DICTIONARY slovak_unaccent (
    Template = unaccent,
    Rules = 'unaccent'
);

CREATE TEXT SEARCH CONFIGURATION slovak_simple_unaccent (COPY = simple);
ALTER TEXT SEARCH CONFIGURATION slovak_simple_unaccent
    ALTER MAPPING FOR asciiword, word, hword, hword_part
    WITH slovak_unaccent, simple;

-- ---------------------------------------------------------------------------
-- Verification
-- ---------------------------------------------------------------------------

SELECT * FROM ts_debug('slovak', 'poistníkovi');
-- Expected lexemes: {poistník}

SELECT to_tsvector('slovak', 'Poistník uzavrel zmluvu')
    @@ to_tsquery('slovak', 'poistník & zmluva');
-- Expected: true
