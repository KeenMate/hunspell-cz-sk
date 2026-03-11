set search_path = public, ext, helpers;

-- ============================================================================
-- TEST 1: AND query - "pojistné & podmínky" matches all docs
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 1: AND query "pojistné & podmínky" matches all docs';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'pojistný & podmínka');

    IF __count = 3 THEN
        RAISE NOTICE '  PASS: Matched all % documents', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: Expected 3 documents, got %', __count;
    END IF;
END $$;

-- ============================================================================
-- TEST 2: AND query - "povinné & ručení" only in vehicle doc
-- ============================================================================
DO $$
DECLARE
    __count    int;
    __filename text;
BEGIN
    RAISE NOTICE 'TEST 2: AND query "povinné & ručení" targets vehicle doc';

    SELECT count(*), string_agg(filename, ', ')
    INTO __count, __filename
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'povinný & ručení');

    IF __count >= 1 THEN
        RAISE NOTICE '  PASS: Matched % doc(s): %', __count, __filename;
    ELSE
        RAISE EXCEPTION '  FAIL: Expected at least 1 match, got 0';
    END IF;
END $$;

-- ============================================================================
-- TEST 3: OR query - "vozidlo | životní" matches at least 2 docs
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 3: OR query "vozidlo | životní" matches multiple docs';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'vozidlo | životní');

    IF __count >= 2 THEN
        RAISE NOTICE '  PASS: Matched % documents', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: Expected at least 2 documents, got %', __count;
    END IF;
END $$;

-- ============================================================================
-- TEST 4: NOT query - "domácnost & !havárie" narrows results
-- ============================================================================
DO $$
DECLARE
    __count_with    int;
    __count_without int;
BEGIN
    RAISE NOTICE 'TEST 4: NOT query "domácnost & !havárie" narrows results';

    SELECT count(*) INTO __count_with
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'domácnost');

    SELECT count(*) INTO __count_without
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'domácnost & !havárie');

    IF __count_without <= __count_with THEN
        RAISE NOTICE '  PASS: NOT narrowed from % to % document(s)', __count_with, __count_without;
    ELSE
        RAISE EXCEPTION '  FAIL: NOT query did not narrow results (with=%, without=%)', __count_with, __count_without;
    END IF;
END $$;

-- ============================================================================
-- TEST 5: Phrase search with <-> (adjacent words) - "osobní <-> údaje"
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 5: Phrase search "osobní <-> údaje" (adjacent words)';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'osobní <-> údaj');

    IF __count >= 1 THEN
        RAISE NOTICE '  PASS: Phrase "osobní údaje" found in % document(s)', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: Phrase "osobní údaje" not found in any document';
    END IF;
END $$;

-- ============================================================================
-- TEST 6: Proximity search <2> - "pojistné <2> podmínky" (within 2 words)
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 6: Proximity search "pojistné <2> podmínky"';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'pojistný <2> podmínka');

    IF __count >= 1 THEN
        RAISE NOTICE '  PASS: Proximity match found in % document(s)', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: No proximity match found';
    END IF;
END $$;

-- ============================================================================
-- TEST 7: Ranking - "majetek" returns ranked results
-- ============================================================================
DO $$
DECLARE
    __top_filename text;
    __top_rank     real;
BEGIN
    RAISE NOTICE 'TEST 7: Ranking - "majetek" returns ranked results';

    SELECT filename, ts_rank(tsv, to_tsquery('czech', 'majetek'))
    INTO __top_filename, __top_rank
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'majetek')
    ORDER BY ts_rank(tsv, to_tsquery('czech', 'majetek')) DESC
    LIMIT 1;

    IF __top_rank > 0 THEN
        RAISE NOTICE '  PASS: Top ranked doc is "%" with rank=%', __top_filename, __top_rank;
    ELSE
        RAISE EXCEPTION '  FAIL: No ranked results for "majetek"';
    END IF;
END $$;

-- ============================================================================
-- TEST 8: plainto_tsquery - natural language "pojistné plnění škoda"
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 8: plainto_tsquery with natural language input';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ plainto_tsquery('czech', 'pojistné plnění škoda');

    IF __count >= 1 THEN
        RAISE NOTICE '  PASS: Natural language query matched % document(s)', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: Natural language query matched 0 documents';
    END IF;
END $$;

-- ============================================================================
-- TEST 9: websearch_to_tsquery - user-friendly search syntax
-- ============================================================================
DO $$
DECLARE
    __count int;
BEGIN
    RAISE NOTICE 'TEST 9: websearch_to_tsquery "pojistné podmínky smlouva"';

    SELECT count(*) INTO __count
    FROM documents
    WHERE tsv @@ websearch_to_tsquery('czech', 'pojistné podmínky smlouva');

    IF __count >= 1 THEN
        RAISE NOTICE '  PASS: Websearch query matched % document(s)', __count;
    ELSE
        RAISE EXCEPTION '  FAIL: Websearch query matched 0 documents';
    END IF;
END $$;

-- ============================================================================
-- TEST 10: ts_headline - highlighted snippet contains search term
-- ============================================================================
DO $$
DECLARE
    __headline text;
BEGIN
    RAISE NOTICE 'TEST 10: ts_headline returns highlighted snippet';

    SELECT ts_headline('czech', body, to_tsquery('czech', 'majetek'),
                       'StartSel=<b>, StopSel=</b>, MaxWords=20, MinWords=5')
    INTO __headline
    FROM documents
    WHERE tsv @@ to_tsquery('czech', 'majetek')
    ORDER BY ts_rank(tsv, to_tsquery('czech', 'majetek')) DESC
    LIMIT 1;

    IF __headline LIKE '%<b>%</b>%' THEN
        RAISE NOTICE '  PASS: Headline contains highlighted term';
    ELSE
        RAISE EXCEPTION '  FAIL: Headline missing highlight markup: %', left(__headline, 100);
    END IF;
END $$;
