set search_path = public, ext, helpers;

-- ============================================================================
-- TEST 1: Documents table has 3 rows
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 1: documents table contains 3 rows';

    SELECT count(*) INTO __count FROM documents;

    IF __count = 3 THEN
        RAISE NOTICE '  PASS: Found % documents', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: Expected 3 documents, got %', __count;
    END IF;
END $$;

-- ============================================================================
-- TEST 2: All documents have non-empty tsvector
-- ============================================================================
DO $$
DECLARE
    __empty_count int;
BEGIN
    RAISE NOTICE 'TEST 2: all documents have non-empty tsvector';

    SELECT count(*) INTO __empty_count
    FROM documents
    WHERE tsv IS NULL OR tsv = ''::tsvector;

    IF __empty_count = 0 THEN
        RAISE NOTICE '  PASS: All documents have populated tsvector';
    ELSE
        RAISE EXCEPTION '  FAIL: % documents have empty tsvector', __empty_count;
    END IF;
END $$;

-- ============================================================================
-- TEST 3: Single-word search - "pojištění" matches all 3 documents
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 3: search for "pojištění" matches all 3 documents';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'pojištění');

    IF __count = 3 THEN
        RAISE NOTICE '  PASS: "pojištění" found in all % documents', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: "pojištění" expected in 3 documents, found in %', __count;
    END IF;
END $$;

-- ============================================================================
-- TEST 4: Stemming - "pojistník" matches same docs as inflected forms
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 4: stemmed search for "pojistník"';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'pojistník');

    IF __count >= 1 THEN
        RAISE NOTICE '  PASS: "pojistník" matched % document(s)', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: "pojistník" matched 0 documents';
    END IF;
END $$;

-- ============================================================================
-- TEST 5: Domain-specific - "povinné ručení" matches at least 1 doc
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 5: search for "povinné ručení"';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'povinný & ručení');

    IF __count >= 1 THEN
        RAISE NOTICE '  PASS: "povinné ručení" matched % document(s)', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: "povinné ručení" matched 0 documents';
    END IF;
END $$;

-- ============================================================================
-- TEST 6: Domain-specific - "chirurgický" matches at least 1 doc
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 6: search for "chirurgický"';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'chirurgický');

    IF __count >= 1 THEN
        RAISE NOTICE '  PASS: "chirurgický" matched % document(s)', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: "chirurgický" matched 0 documents';
    END IF;
END $$;

-- ============================================================================
-- TEST 7: Domain-specific - "domácnost" matches at least 1 doc
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 7: search for "domácnost"';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'domácnost');

    IF __count >= 1 THEN
        RAISE NOTICE '  PASS: "domácnost" matched % document(s)', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: "domácnost" matched 0 documents';
    END IF;
END $$;
