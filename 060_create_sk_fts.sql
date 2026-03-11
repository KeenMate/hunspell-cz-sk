set search_path = public, ext, helpers;

select start_version_update('1', 'Slovak FTS Setup', _component := 'hunspell_fts_sk');

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
-- Verification queries
-- ---------------------------------------------------------------------------

SELECT * FROM ts_debug('slovak', 'poistníkovi');
SELECT * FROM ts_debug('slovak', 'poisťovňa');

select stop_version_update('1', _component := 'hunspell_fts_sk');
