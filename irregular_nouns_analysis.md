# Irregular Nouns Analysis

## Summary

After running the fixer, bare entries in the PDF report dropped from 2,286 → 721 (68% reduction). The remaining 721 bare words were analyzed for irregular noun groups relevant to search (e.g. "pojisteni dum" should find "pojisteni domu").

**33 irregular noun groups** were found covering **109 of 721 bare words**.

## Irregular Noun Groups Found

### Stem Vowel Alternation (ů→o)

| Base | Forms in report | Also in dict bare | Pattern |
|------|----------------|-------------------|---------|
| **dům** | dům, domu, domě, domem, domy, domů, domech (7) | domům | ů→o (dům→dom-) |
| **dvůr** | dvůr (1) | dvora, dvoru, dvorem, dvoře, dvory, dvorů, dvorům, dvorech | ů→o (dvůr→dvor-) |
| **kůň** | koně (1) | kůň, koňmi, koněm | ů→o (kůň→koň-) |

### Fleeting Vowel (e disappears in oblique forms)

| Base | Forms in report | Also in dict bare | Pattern |
|------|----------------|-------------------|---------|
| **stupeň** | stupeň, stupně, stupni, stupněm, stupňů (5) | stupňům | stupeň→stupň- |
| **účet** | účet, účtu, účty, účtů (4) | účtem, účtům, účtech | účet→účt- |
| **příjem** | příjem, příjmy, příjmů, příjmech (4) | příjmu, příjmem, příjmům | příjem→příjm- |
| **pronájem** | pronájem, pronájmu, pronájmem, pronájmů (4) | pronájmy, pronájmům, pronájmech | pronájem→pronájm- |
| **zájem** | zájem, zájmu, zájmy, zájmů (4) | zájmem, zájmům, zájmech | zájem→zájm- |
| **povodeň** | povodeň, povodně, povodni, povodní (4) | povodním, povodních, povodněmi | povodeň→povodn- |
| **pojem** | pojem, pojmy, pojmů (3) | pojmem, pojmům, pojmech | pojem→pojm- |
| **název** | název, názvu, názvem (3) | názvy, názvů, názvům, názvech | název→názv- |
| **pohřeb** | pohřeb, pohřbu, pohřbem (3) | pohřby, pohřbů, pohřbům, pohřbech | pohřeb→pohřb- |
| **úroveň** | úroveň, úrovně (2) | úrovni, úrovní, úrovním, úrovních, úrovněmi | úroveň→úrovn- |
| **týden** | týdne, týdnu (2) | týden, týdnem, týdny, týdnech | týden→týdn- |
| **nájem** | nájmu, nájmem (2) | nájem, nájmy, nájmů | nájem→nájm- |
| **výpočet** | výpočet, výpočtu (2) | výpočtem, výpočty, výpočtů | výpočet→výpočt- |
| **den** | dnů (1) | den, dnům, dnech | den→dn- |

### Suppletive / Highly Irregular

| Base | Forms in report | Also in dict bare | Pattern |
|------|----------------|-------------------|---------|
| **člověk** | člověka, člověku, člověkem, lidí (4) | člověk, člověče, lidé, lidmi | člověk→lidé (suppletive) |
| **rok** | rok, roku, roce, roky (4) | rokem, roků, rokům, rocích, let, letech, lety | suppletive plural (let/letech) |
| **dítě** | dítě, dítěte, děti (3) | dítěti, dětí, dětem, dětmi, dětech | dítě→děti (suppletive) |
| **oko** | očí, očích (2) | oči, očím, očima | oko→oči |
| **vítr** | vítr, větru (2) | větrem, větry, větrů, větrům, větrech | í→ě (vítr→větr-) |

### Regular but All Bare (insurance domain)

| Base | Forms in report | Also in dict bare | Pattern |
|------|----------------|-------------------|---------|
| **zákrok** | zákrok, zákroku, zákroky, zákroků, zákrocích (5) | zákrokem, zákrokům | k→c in loc.pl. |
| **nárok** | nárok, nároku, nároky, nároků (4) | nárokem, nárokům, nárocích | regular |
| **vznik** | vznik, vzniku, vznikem (3) | vzniky, vzniků | regular |
| **zánik** | zánik, zániku, zánikem (3) | zániky, zánikům | regular |
| **únik** | únik, úniku, únikem (3) | úniky, úniků | regular |
| **výpověď** | výpověď, výpovědi, výpovědí (3) | výpovědím, výpovědích, výpověďmi | regular |

### -ník Nouns (animate k→c in plural)

| Base | Forms in report | Also in dict bare | Pattern |
|------|----------------|-------------------|---------|
| **účastník** | účastník, účastníka, účastníkem, účastníku, účastníků, účastníkům, účastníci (7) | účastníkovi, účastníky | animate |
| **pojistník** | pojistník, pojistníka, pojistníkem, pojistníkovi (4) | pojistníky, pojistníků, pojistníkům, pojistníci | animate |
| **vlastník** | vlastník, vlastníka, vlastníkem, vlastníků (4) | vlastníkovi, vlastníky, vlastníkům, vlastníci | animate |
| **zákoník** | zákoník, zákoníku, zákoníkem (3) | zákoníky, zákoníků | inanimate |
| **sazebník** | sazebník, sazebníku, sazebníkem (3) | sazebníky, sazebníků | inanimate |

## Remaining Bare Words by Category

Beyond the 33 groups above, the 721 bare words break down as:

| Category | Count | Examples |
|----------|-------|---------|
| **Adverbs (-ně)** | 106 | aktuálně, bezplatně, dlouhodobě, elektronicky |
| **-ník words** | 59 | nájemníkem, opatrovník, podnájemníků |
| **Instrumental (-em)** | 42 | bleskem, mrazákem, pohřbem |
| **Genitive plural (-ů)** | 34 | boltců, disků, léků, příznaků |
| **Adverbs (-icky)** | 11 | automaticky, elektronicky, prakticky |
| **Locative (-ště)** | 9 | bydliště, pracoviště, staveniště |
| **Adverbs (-ově)** | 4 | celkově, majetkově, časově |
| **Abbreviations/particles** | ~50 | apod, alespoň, avšak, cm, cca, eu |
| **Proper nouns** | ~30 | brno, albánie, bosna, evropa |

Note: categories overlap — a word can match multiple suffix patterns.

## Recommendations for Search

For search use case (e.g. "pojisteni dum" → finds "pojisteni domu"):

### Option 1: Synonym Map (recommended for search engines)
Create a synonym/alias file mapping all forms to a canonical form:
```
dům,domu,domě,domem,domy,domů,domům,domech → dům
dítě,dítěte,dítěti,děti,dětí,dětem,dětmi,dětech → dítě
rok,roku,roce,rokem,roky,roků,rokům,rocích,let,letech,léta,lety → rok
```
Best for Solr/Elasticsearch. Easiest to implement.

### Option 2: Custom Affix Rules
Add new affix flags in the .aff file specifically for irregular stem-changing patterns. More complex but the proper hunspell solution. Would require one flag per alternation pattern.

### Option 3: Both
Use custom affix rules in the hunspell dictionary for what can be expressed, and a synonym map for truly suppletive forms (člověk→lidé, rok→let).

## Next Steps

- [ ] Decide which approach to pursue (synonym map vs custom affix rules)
- [ ] For "regular but all bare" groups — investigate why the fixer missed them (may need lower thresholds or additional affix patterns)
- [ ] The -ník words (59 in bare list) could potentially be consolidated with a dedicated affix flag
- [ ] Adverbs (106 bare) are standalone forms — no action needed for search since they don't decline

## Files

- `analyze_irregular.py` — script that produced this analysis
- `report_fixed.txt` — full checker report after fixes
- `cs_cz_fixed.dict` — the fixed dictionary
- `/tmp/bare_words_721.txt` — extracted bare words list (regenerate from report_fixed.txt if lost)
- `/tmp/bare_entries.txt` — all bare entries from dict (regenerate from cs_cz_fixed.dict if lost)
