-- ============================================================================
-- Deployment verification for Czech & Slovak FTS dictionaries
-- ============================================================================
-- Run against the target database after installing dictionaries.
-- Uses the debee test format: RAISE NOTICE for PASS, RAISE EXCEPTION for FAIL.
-- ============================================================================

-- ============================================================================
-- TEST 1: czech_hunspell dictionary exists with correct settings
-- ============================================================================
DO $$
DECLARE
    __template text;
    __options  text;
BEGIN
    RAISE NOTICE 'TEST 1: czech_hunspell dictionary definition';

    SELECT t.tmplname, d.dictinitoption
    INTO __template, __options
    FROM pg_ts_dict d
    JOIN pg_ts_template t ON d.dicttemplate = t.oid
    WHERE d.dictname = 'czech_hunspell';

    IF NOT FOUND THEN
        RAISE EXCEPTION '  FAIL: czech_hunspell dictionary not found';
    END IF;

    IF __template <> 'ispell' THEN
        RAISE EXCEPTION '  FAIL: expected template "ispell", got "%"', __template;
    END IF;

    IF __options NOT LIKE '%dictfile = ''cs_cz''%' THEN
        RAISE EXCEPTION '  FAIL: DictFile not set to cs_cz. Options: %', __options;
    END IF;

    IF __options NOT LIKE '%afffile = ''cs_cz''%' THEN
        RAISE EXCEPTION '  FAIL: AffFile not set to cs_cz. Options: %', __options;
    END IF;

    IF __options NOT LIKE '%stopwords = ''czech''%' THEN
        RAISE EXCEPTION '  FAIL: StopWords not set to czech. Options: %', __options;
    END IF;

    RAISE NOTICE '  PASS: template=%, options=%', __template, __options;
END $$;

-- ============================================================================
-- TEST 2: czech_simple dictionary exists with correct settings
-- ============================================================================
DO $$
DECLARE
    __template text;
    __options  text;
BEGIN
    RAISE NOTICE 'TEST 2: czech_simple dictionary definition';

    SELECT t.tmplname, d.dictinitoption
    INTO __template, __options
    FROM pg_ts_dict d
    JOIN pg_ts_template t ON d.dicttemplate = t.oid
    WHERE d.dictname = 'czech_simple';

    IF NOT FOUND THEN
        RAISE EXCEPTION '  FAIL: czech_simple dictionary not found';
    END IF;

    IF __template <> 'simple' THEN
        RAISE EXCEPTION '  FAIL: expected template "simple", got "%"', __template;
    END IF;

    IF __options NOT LIKE '%stopwords = ''czech''%' THEN
        RAISE EXCEPTION '  FAIL: StopWords not set to czech. Options: %', __options;
    END IF;

    RAISE NOTICE '  PASS: template=%, options=%', __template, __options;
END $$;

-- ============================================================================
-- TEST 3: czech_unaccent dictionary exists with correct settings
-- ============================================================================
DO $$
DECLARE
    __template text;
    __options  text;
BEGIN
    RAISE NOTICE 'TEST 3: czech_unaccent dictionary definition';

    SELECT t.tmplname, d.dictinitoption
    INTO __template, __options
    FROM pg_ts_dict d
    JOIN pg_ts_template t ON d.dicttemplate = t.oid
    WHERE d.dictname = 'czech_unaccent';

    IF NOT FOUND THEN
        RAISE EXCEPTION '  FAIL: czech_unaccent dictionary not found';
    END IF;

    IF __template <> 'unaccent' THEN
        RAISE EXCEPTION '  FAIL: expected template "unaccent", got "%"', __template;
    END IF;

    IF __options NOT LIKE '%rules = ''unaccent''%' THEN
        RAISE EXCEPTION '  FAIL: Rules not set to unaccent. Options: %', __options;
    END IF;

    RAISE NOTICE '  PASS: template=%, options=%', __template, __options;
END $$;

-- ============================================================================
-- TEST 4: slovak_hunspell dictionary exists with correct settings
-- ============================================================================
DO $$
DECLARE
    __template text;
    __options  text;
BEGIN
    RAISE NOTICE 'TEST 4: slovak_hunspell dictionary definition';

    SELECT t.tmplname, d.dictinitoption
    INTO __template, __options
    FROM pg_ts_dict d
    JOIN pg_ts_template t ON d.dicttemplate = t.oid
    WHERE d.dictname = 'slovak_hunspell';

    IF NOT FOUND THEN
        RAISE EXCEPTION '  FAIL: slovak_hunspell dictionary not found';
    END IF;

    IF __template <> 'ispell' THEN
        RAISE EXCEPTION '  FAIL: expected template "ispell", got "%"', __template;
    END IF;

    IF __options NOT LIKE '%dictfile = ''sk_sk''%' THEN
        RAISE EXCEPTION '  FAIL: DictFile not set to sk_sk. Options: %', __options;
    END IF;

    IF __options NOT LIKE '%afffile = ''sk_sk''%' THEN
        RAISE EXCEPTION '  FAIL: AffFile not set to sk_sk. Options: %', __options;
    END IF;

    IF __options NOT LIKE '%stopwords = ''slovak''%' THEN
        RAISE EXCEPTION '  FAIL: StopWords not set to slovak. Options: %', __options;
    END IF;

    RAISE NOTICE '  PASS: template=%, options=%', __template, __options;
END $$;

-- ============================================================================
-- TEST 5: slovak_simple dictionary exists with correct settings
-- ============================================================================
DO $$
DECLARE
    __template text;
    __options  text;
BEGIN
    RAISE NOTICE 'TEST 5: slovak_simple dictionary definition';

    SELECT t.tmplname, d.dictinitoption
    INTO __template, __options
    FROM pg_ts_dict d
    JOIN pg_ts_template t ON d.dicttemplate = t.oid
    WHERE d.dictname = 'slovak_simple';

    IF NOT FOUND THEN
        RAISE EXCEPTION '  FAIL: slovak_simple dictionary not found';
    END IF;

    IF __template <> 'simple' THEN
        RAISE EXCEPTION '  FAIL: expected template "simple", got "%"', __template;
    END IF;

    IF __options NOT LIKE '%stopwords = ''slovak''%' THEN
        RAISE EXCEPTION '  FAIL: StopWords not set to slovak. Options: %', __options;
    END IF;

    RAISE NOTICE '  PASS: template=%, options=%', __template, __options;
END $$;

-- ============================================================================
-- TEST 6: slovak_unaccent dictionary exists with correct settings
-- ============================================================================
DO $$
DECLARE
    __template text;
    __options  text;
BEGIN
    RAISE NOTICE 'TEST 6: slovak_unaccent dictionary definition';

    SELECT t.tmplname, d.dictinitoption
    INTO __template, __options
    FROM pg_ts_dict d
    JOIN pg_ts_template t ON d.dicttemplate = t.oid
    WHERE d.dictname = 'slovak_unaccent';

    IF NOT FOUND THEN
        RAISE EXCEPTION '  FAIL: slovak_unaccent dictionary not found';
    END IF;

    IF __template <> 'unaccent' THEN
        RAISE EXCEPTION '  FAIL: expected template "unaccent", got "%"', __template;
    END IF;

    IF __options NOT LIKE '%rules = ''unaccent''%' THEN
        RAISE EXCEPTION '  FAIL: Rules not set to unaccent. Options: %', __options;
    END IF;

    RAISE NOTICE '  PASS: template=%, options=%', __template, __options;
END $$;

-- ============================================================================
-- TEST 7: Czech text search configuration exists
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'TEST 7: czech text search configuration exists';

    IF EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname = 'czech'
    ) THEN
        RAISE NOTICE '  PASS: czech configuration found';
    ELSE
        RAISE EXCEPTION '  FAIL: czech configuration not found';
    END IF;
END $$;

-- ============================================================================
-- TEST 8: Czech hunspell stemming works (pojistníkovi -> pojistník)
-- ============================================================================
DO $$
DECLARE
    __lexemes text;
BEGIN
    RAISE NOTICE 'TEST 8: czech hunspell stemming (pojistníkovi -> pojistník)';

    SELECT array_to_string(tsvector_to_array(to_tsvector('czech', 'pojistníkovi')), ',')
    INTO __lexemes;

    IF __lexemes LIKE '%pojistník%' THEN
        RAISE NOTICE '  PASS: stemmed to %', __lexemes;
    ELSE
        RAISE EXCEPTION '  FAIL: expected "pojistník", got "%"', __lexemes;
    END IF;
END $$;

-- ============================================================================
-- TEST 9: Czech hunspell stemming works (pojištění -> various forms)
-- ============================================================================
DO $$
DECLARE
    __result boolean;
BEGIN
    RAISE NOTICE 'TEST 9: czech hunspell query matching (pojištění)';

    SELECT to_tsvector('czech', 'Pojistník uzavřel smlouvu o pojištění')
        @@ to_tsquery('czech', 'pojištění')
    INTO __result;

    IF __result THEN
        RAISE NOTICE '  PASS: pojištění matched in sample text';
    ELSE
        RAISE EXCEPTION '  FAIL: pojištění did not match in sample text';
    END IF;
END $$;

-- ============================================================================
-- TEST 10: Czech config chains hunspell -> simple (unknown word falls through)
-- ============================================================================
DO $$
DECLARE
    __lexemes text;
BEGIN
    RAISE NOTICE 'TEST 10: unknown word falls through to czech_simple';

    SELECT array_to_string(tsvector_to_array(to_tsvector('czech', 'xyzneexistuje')), ',')
    INTO __lexemes;

    IF __lexemes = 'xyzneexistuje' THEN
        RAISE NOTICE '  PASS: unknown word passed through as-is: %', __lexemes;
    ELSE
        RAISE EXCEPTION '  FAIL: expected "xyzneexistuje", got "%"', __lexemes;
    END IF;
END $$;

-- ============================================================================
-- TEST 11: Czech stop words are active ("a", "nebo" should be removed)
-- ============================================================================
DO $$
DECLARE
    __result text[];
BEGIN
    RAISE NOTICE 'TEST 11: czech stop words file loaded (czech_simple filters "aby")';

    -- ts_lexize on the simple dictionary returns {} for stop words (recognized & filtered).
    -- A word not in the stop list returns NULL (not recognized by this dictionary).
    SELECT ts_lexize('czech_simple', 'aby') INTO __result;

    IF __result = '{}' THEN
        RAISE NOTICE '  PASS: "aby" recognized as stop word by czech_simple';
    ELSE
        RAISE EXCEPTION '  FAIL: expected empty array {} for stop word, got "%"', __result;
    END IF;
END $$;

-- ============================================================================
-- TEST 12: immutable_unaccent function exists
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'TEST 12: immutable_unaccent function exists';

    IF EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'immutable_unaccent'
    ) THEN
        RAISE NOTICE '  PASS: immutable_unaccent function found';
    ELSE
        RAISE EXCEPTION '  FAIL: immutable_unaccent function not found';
    END IF;
END $$;

-- ============================================================================
-- TEST 13: immutable_unaccent works correctly
-- ============================================================================
DO $$
DECLARE
    __result text;
BEGIN
    RAISE NOTICE 'TEST 13: immutable_unaccent removes diacritics';

    SELECT public.immutable_unaccent('příšerně žluťoučký kůň') INTO __result;

    IF __result = 'priserne zlutoucky kun' THEN
        RAISE NOTICE '  PASS: "%"', __result;
    ELSE
        RAISE EXCEPTION '  FAIL: expected "priserne zlutoucky kun", got "%"', __result;
    END IF;
END $$;

-- ============================================================================
-- TEST 14: czech_simple_unaccent configuration exists
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'TEST 14: czech_simple_unaccent configuration exists';

    IF EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname = 'czech_simple_unaccent'
    ) THEN
        RAISE NOTICE '  PASS: czech_simple_unaccent configuration found';
    ELSE
        RAISE EXCEPTION '  FAIL: czech_simple_unaccent configuration not found';
    END IF;
END $$;

-- ============================================================================
-- TEST 15: Unaccented search works (accent-insensitive matching)
-- ============================================================================
DO $$
DECLARE
    __result boolean;
BEGIN
    RAISE NOTICE 'TEST 15: accent-insensitive search via czech_simple_unaccent';

    SELECT to_tsvector('czech_simple_unaccent', public.immutable_unaccent('pojištění'))
        @@ to_tsquery('czech_simple_unaccent', public.immutable_unaccent('pojisteni'))
    INTO __result;

    IF __result THEN
        RAISE NOTICE '  PASS: unaccented "pojisteni" matched "pojištění"';
    ELSE
        RAISE EXCEPTION '  FAIL: unaccented search did not match';
    END IF;
END $$;

-- ============================================================================
-- TEST 16: Slovak text search configuration exists
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'TEST 16: slovak text search configuration exists';

    IF EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname = 'slovak'
    ) THEN
        RAISE NOTICE '  PASS: slovak configuration found';
    ELSE
        RAISE EXCEPTION '  FAIL: slovak configuration not found';
    END IF;
END $$;

-- ============================================================================
-- TEST 17: Slovak hunspell stemming works (poistníkovi -> poistník)
-- ============================================================================
DO $$
DECLARE
    __lexemes text;
BEGIN
    RAISE NOTICE 'TEST 17: slovak hunspell stemming (poistníkovi -> poistník)';

    SELECT array_to_string(tsvector_to_array(to_tsvector('slovak', 'poistníkovi')), ',')
    INTO __lexemes;

    IF __lexemes LIKE '%poistník%' THEN
        RAISE NOTICE '  PASS: stemmed to %', __lexemes;
    ELSE
        RAISE EXCEPTION '  FAIL: expected "poistník", got "%"', __lexemes;
    END IF;
END $$;

-- ============================================================================
-- TEST 18: Slovak hunspell query matching
-- ============================================================================
DO $$
DECLARE
    __result boolean;
BEGIN
    RAISE NOTICE 'TEST 18: slovak hunspell query matching';

    SELECT to_tsvector('slovak', 'Poistník uzavrel zmluvu')
        @@ to_tsquery('slovak', 'poistník & zmluva')
    INTO __result;

    IF __result THEN
        RAISE NOTICE '  PASS: "poistník & zmluva" matched in sample text';
    ELSE
        RAISE EXCEPTION '  FAIL: query did not match in sample text';
    END IF;
END $$;

-- ============================================================================
-- TEST 19: Slovak simple_unaccent configuration exists
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'TEST 19: slovak_simple_unaccent configuration exists';

    IF EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname = 'slovak_simple_unaccent'
    ) THEN
        RAISE NOTICE '  PASS: slovak_simple_unaccent configuration found';
    ELSE
        RAISE EXCEPTION '  FAIL: slovak_simple_unaccent configuration not found';
    END IF;
END $$;

-- ============================================================================
-- SUMMARY
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE 'All 19 deployment tests passed.';
    RAISE NOTICE '====================================';
END $$;
