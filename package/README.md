# Hunspell slovníky pro PostgreSQL fulltextové vyhledávání (CZ + SK)

## Přehled

Tento balíček obsahuje opravené a rozšířené hunspell slovníky pro **češtinu** a **slovenštinu**, optimalizované pro fulltextové vyhledávání (FTS) v PostgreSQL. Umožňují správné stemmování -- vyhledání libovolného tvaru slova (např. "pojistníkovi") správně najde základní tvar ("pojistník") i všechny jeho skloňované tvary.

## Obsah balíčku

```
package/
├── README.md
├── tsearch_data/
│   ├── cs_cz.dict              -- český slovník (387 959 záznamů)
│   ├── cs_cz.affix             -- česká pravidla přípon/předpon
│   ├── czech.stop              -- česká stop slova (422 slov)
│   ├── sk_sk.dict              -- slovenský slovník (155 076 záznamů)
│   ├── sk_sk.affix             -- slovenská pravidla přípon/předpon
│   └── slovak.stop             -- slovenská stop slova (418 slov)
├── install_czech_fts.sql       -- CZ: slovníky + konfigurace + unaccent podpora
└── install_slovak_fts.sql      -- SK: slovníky + konfigurace + unaccent podpora
```

## Instalace

### Předpoklady

- PostgreSQL 14+
- Rozšíření `unaccent` (pro unaccent fallback v obou jazycích)

### Krok 1: Nasazení souborů slovníku

Zkopírujte soubory z `tsearch_data/` do adresáře `tsearch_data` vaší PostgreSQL instance:

```bash
# Typické umístění:
#   Linux:   /usr/share/postgresql/<verze>/tsearch_data/
#   Windows: C:\Program Files\PostgreSQL\<verze>\share\tsearch_data\
#   Docker:  /usr/local/share/postgresql/tsearch_data/

# Čeština
cp tsearch_data/cs_cz.dict   <PGDATA>/tsearch_data/
cp tsearch_data/cs_cz.affix  <PGDATA>/tsearch_data/
cp tsearch_data/czech.stop   <PGDATA>/tsearch_data/

# Slovenština
cp tsearch_data/sk_sk.dict   <PGDATA>/tsearch_data/
cp tsearch_data/sk_sk.affix  <PGDATA>/tsearch_data/
cp tsearch_data/slovak.stop  <PGDATA>/tsearch_data/
```

**Poznámka:** PostgreSQL musí mít práva ke čtení těchto souborů. Na Linuxu ověřte vlastníka (`postgres:postgres`) a oprávnění (`644`).

### Krok 2: Spuštění instalačních skriptů

```sql
-- Čeština (slovníky + konfigurace + unaccent podpora):
\i install_czech_fts.sql

-- Slovenština (slovníky + konfigurace + unaccent podpora):
\i install_slovak_fts.sql
```

### Krok 3: Ověření

```sql
-- Čeština:
SELECT * FROM ts_debug('czech', 'pojistníkovi');
-- lexémy: {pojistník}

SELECT to_tsvector('czech', 'Pojistník uzavřel smlouvu')
    @@ to_tsquery('czech', 'pojistník & smlouva');
-- true

-- Slovenština:
SELECT * FROM ts_debug('slovak', 'poistníkovi');
-- lexémy: {poistník}

SELECT to_tsvector('slovak', 'Poistník uzavrel zmluvu')
    @@ to_tsquery('slovak', 'poistník & zmluva');
-- true
```

## Co balíček vytváří

### Čeština (`install_czech_fts.sql`)

| Objekt | Typ | Popis |
|--------|-----|-------|
| `czech_hunspell` | TEXT SEARCH DICTIONARY | Hunspell stemmování s českými pravidly |
| `czech_simple` | TEXT SEARCH DICTIONARY | Jednoduchý fallback pro neznámá slova |
| `czech` | TEXT SEARCH CONFIGURATION | Řetězení: hunspell → simple |
| `immutable_unaccent` | FUNCTION | Neměnná obálka pro `unaccent()` (potřebná pro generované sloupce) |
| `czech_unaccent` | TEXT SEARCH DICTIONARY | Unaccent filtr |
| `czech_simple_unaccent` | TEXT SEARCH CONFIGURATION | Vyhledávání bez diakritiky |

### Slovenština (`install_slovak_fts.sql`)

| Objekt | Typ | Popis |
|--------|-----|-------|
| `slovak_hunspell` | TEXT SEARCH DICTIONARY | Hunspell stemmování se slovenskými pravidly |
| `slovak_simple` | TEXT SEARCH DICTIONARY | Jednoduchý fallback pro neznámá slova |
| `slovak` | TEXT SEARCH CONFIGURATION | Řetězení: hunspell → simple |
| `slovak_unaccent` | TEXT SEARCH DICTIONARY | Unaccent filtr |
| `slovak_simple_unaccent` | TEXT SEARCH CONFIGURATION | Vyhledávání bez diakritiky |

## Použití ve vaší aplikaci

Balíček vytváří pouze slovníky a konfigurace. Tabulky, sloupce a indexy si vytvoříte sami podle potřeb vaší aplikace. Příklad:

```sql
-- Tabulka s hunspell tsvectorem
CREATE TABLE documents (
    id serial PRIMARY KEY,
    body text,
    tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('czech', coalesce(body, ''))
    ) STORED
);
CREATE INDEX idx_documents_tsv ON documents USING gin(tsv);

-- Volitelně: sloupec pro vyhledávání bez diakritiky
ALTER TABLE documents ADD COLUMN tsv_unaccent tsvector GENERATED ALWAYS AS (
    to_tsvector('czech_simple_unaccent', immutable_unaccent(coalesce(body, '')))
) STORED;
CREATE INDEX idx_documents_tsv_unaccent ON documents USING gin(tsv_unaccent);
```

### Strategie vyhledávání

1. **S diakritikou** -- `to_tsquery('czech', ...)` proti `tsv` sloupci (hunspell stemmování)
2. **Bez diakritiky** -- `to_tsquery('czech_simple_unaccent', immutable_unaccent(...))` proti `tsv_unaccent` sloupci

---

## Český slovník -- co bylo změněno

Původní český hunspell slovník (z balíčku LibreOffice/OpenOffice) měl zásadní nedostatky: velké množství slov bylo uloženo jako samostatné "holé" záznamy bez příponových vlajek, takže PostgreSQL nedokázal provést stemmování zpět na základní tvar.

### Problém

Původní slovník obsahoval **524 209 záznamů**, ale ~190 000 z nich byly holé tvary bez vazby na základní tvar. Např. místo `dům/R` (generující domu, domě, domem...) měl každý tvar zvlášť -- PostgreSQL pak nedokázal rozpoznat, že "domu" je tvar slova "dům".

### Opravy

#### 1. Konsolidace reverzní morfologií

Automatická analýza zpětně aplikuje příponová pravidla a hledá holé záznamy sloučitelné pod otagovaný základní tvar:

- **21 010 základních tvarů otagováno**
- **242 existujících záznamů obohaceno** o další vlajky
- **135 817 redundantních tvarů odstraněno**
- **378 slovesných duplicit odstraněno**

Algoritmus sloučí skupinu pouze pokud alespoň 60 % očekávaných tvarů existuje a min. 3 se shodují.

#### 2. Vlastní příponová pravidla pro nepravidelná podstatná jména

| Vlajka | Vzor | Příklad | Popis |
|--------|------|---------|-------|
| **R** | ů → o | dům → domu, domě... | Alternace samohlásky (dům, dvůr, kůň, stůl, důl, vůl) |
| **J** | prchavé -e- (muž.) | příjem → příjmu... | Obnovení souhláskové skupiny (příjem, nájem, účet, název...) |
| **Q** | prchavé -e- (žen.) | povodeň → povodně... | Ženská varianta (povodeň, úroveň) |
| **T** | k → c (životná) | pojistník → pojistníci | Palatalizace v nom. pl. |
| **U** | k → c (neživotná) | nárok → nárocích | Palatalizace v lok. pl. |

#### 3. Výsledky

| Metrika | Původní | Po opravě |
|---------|---------|-----------|
| Záznamy ve slovníku | 524 209 | 387 959 |
| Expandované tvary | — | 1 060 998 |
| Zbývající holé záznamy | ~190 000+ | 51 632 |

Všechny odstraněné tvary validovány -- žádná ztráta pokrytí.

### Praktický dopad

```sql
-- Před opravou: "dům" NENAŠLO dokumenty obsahující "domu"
-- Po opravě:
SELECT to_tsvector('czech', 'pojistník uzavřel smlouvu na pojištění domu')
    @@ to_tsquery('czech', 'dům');
-- true

SELECT to_tsvector('czech', 'příjmy z pronájmu bytů')
    @@ to_tsquery('czech', 'příjem');
-- true
```

---

## Slovenský slovník -- co bylo změněno

Slovenský hunspell slovník (LibreOffice, verze 2.4.7) byl na tom výrazně lépe než český -- má 3 438 příponových pravidel ve 28 vlajkách s bohatým morfologickým tagováním. Přesto obsahoval **68 743 holých záznamů** ze 160 684 celkových.

### Opravy

#### Konsolidace reverzní morfologií

Stejný algoritmus jako pro češtinu, aplikovaný na slovenský afixový systém:

- **668 základních tvarů otagováno**
- **314 existujících záznamů obohaceno** o další vlajky
- **4 116 redundantních tvarů odstraněno**

#### Výsledky

| Metrika | Původní | Po opravě |
|---------|---------|-----------|
| Záznamy ve slovníku | 160 684 | 155 076 |
| Expandované tvary | 2 816 146 | 2 816 739 |
| Zbývající holé záznamy | 68 743 | 64 024 |

Všechny odstraněné tvary validovány -- žádná ztráta pokrytí.

#### Testováno na pojistných dokumentech

Slovník ověřen na slovenských pojistných dokumentech — pokrytí 78–85 % slov se správným stemmováním. Neznámá slova jsou hlavně pojistné složeniny a anglické výrazy z PDF.

---

## Poznámky

- Oba slovníky jsou v kódování UTF-8
- Český affix soubor: 18 původních vlajek + 5 vlastních (R, J, Q, T, U)
- Slovenský affix soubor: 28 vlajek (z originálního balíčku, bez vlastních úprav -- jen konsolidace holých záznamů)
- Slovenský slovník má výrazně bohatší sadu příponových pravidel (3 438 vs 335 pro češtinu)
- Funkce `immutable_unaccent` je potřebná, protože PostgreSQL vyžaduje `IMMUTABLE` výrazy v generovaných sloupcích, ale vestavěná `unaccent()` je deklarovaná pouze jako `STABLE`
