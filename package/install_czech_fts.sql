-- ============================================================================
-- Czech FTS dictionaries for PostgreSQL
-- ============================================================================
-- Prerequisites:
--   1. Copy cs_cz.dict, cs_cz.affix, czech.stop to PostgreSQL's tsearch_data/
--   2. Extension 'unaccent' must be installed
-- ============================================================================

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
-- Unaccent support (for accent-insensitive search)
-- ---------------------------------------------------------------------------

-- Immutable wrapper for unaccent — needed for GENERATED ALWAYS AS columns,
-- because PostgreSQL's built-in unaccent() is declared STABLE, not IMMUTABLE.
-- The unaccent rules never change at runtime, so this is safe.
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
    RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
AS $$ SELECT unaccent($1); $$;

-- Simple text search config with unaccent filter
CREATE TEXT SEARCH DICTIONARY czech_unaccent (
    Template = unaccent,
    Rules = 'unaccent'
);

CREATE TEXT SEARCH CONFIGURATION czech_simple_unaccent (COPY = simple);
ALTER TEXT SEARCH CONFIGURATION czech_simple_unaccent
    ALTER MAPPING FOR asciiword, word, hword, hword_part
    WITH czech_unaccent, simple;

-- ---------------------------------------------------------------------------
-- Verification
-- ---------------------------------------------------------------------------

SELECT * FROM ts_debug('czech', 'pojistníkovi');
-- Expected lexemes: {pojistník}

SELECT to_tsvector('czech', 'Pojistník uzavřel smlouvu')
    @@ to_tsquery('czech', 'pojistník & smlouva');
-- Expected: true
