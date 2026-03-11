#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze irregular noun groups among bare words from the hunspell report.

Finds groups of bare words that belong together (same lemma, different cases)
but can't be consolidated by affix rules due to stem alternations.
"""
import sys

def load_words(path):
    with open(path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def main():
    # Load bare words from report
    bare_words = load_words('/tmp/bare_words_721.txt')
    # Load bare entries from dict
    dict_bare = load_words('/tmp/bare_entries.txt')

    print(f"BARE words from report: {len(bare_words)}")
    print(f"Bare entries in dict: {len(dict_bare)}")

    # Define irregular noun groups - each is (base_form, [all_forms], pattern)
    groups = [
        # === Stem vowel alternation: \u016f \u2192 o ===
        ('d\u016fm', ['d\u016fm','domu','dom\u011b','domem','domy','dom\u016f','dom\u016fm','domech'], '\u016f\u2192o (d\u016fm\u2192dom-)'),
        ('dv\u016fr', ['dv\u016fr','dvora','dvoru','dvorem','dvo\u0159e','dvory','dvor\u016f','dvor\u016fm','dvorech'], '\u016f\u2192o (dv\u016fr\u2192dvor-)'),
        ('k\u016f\u0148', ['k\u016f\u0148','kon\u011b','koni','kon\u00edm','kon\u00edch','ko\u0148mi','kon\u00ed','kon\u011bm'], '\u016f\u2192o (k\u016f\u0148\u2192ko\u0148-)'),
        ('st\u016fl', ['st\u016fl','stolu','stolem','stole','stoly','stol\u016f','stol\u016fm','stolech'], '\u016f\u2192o (st\u016fl\u2192stol-)'),

        # === Fleeting vowel (e disappears in oblique) ===
        ('den', ['den','dne','dni','dnu','dnem','dn\u016f','dn\u016fm','dnech','dny'], 'fleeting e (den\u2192dn-)'),
        ('t\u00fdden', ['t\u00fdden','t\u00fddne','t\u00fddnu','t\u00fddnem','t\u00fddny','t\u00fcdn\u016f','t\u00fcdn\u016fm','t\u00fddnech'], 'fleeting e (t\u00fdden\u2192t\u00fddn-)'),
        ('\u00fa\u010det', ['\u00fa\u010det','\u00fa\u010dtu','\u00fa\u010dtem','\u00fa\u010dty','\u00fa\u010dt\u016f','\u00fa\u010dt\u016fm','\u00fa\u010dtech'], 'fleeting e (\u00fa\u010det\u2192\u00fa\u010dt-)'),
        ('pojem', ['pojem','pojmu','pojmem','pojmy','pojm\u016f','pojm\u016fm','pojmech'], 'fleeting e (pojem\u2192pojm-)'),
        ('p\u0159\u00edjem', ['p\u0159\u00edjem','p\u0159\u00edjmu','p\u0159\u00edjmem','p\u0159\u00edjmy','p\u0159\u00edjm\u016f','p\u0159\u00edjm\u016fm','p\u0159\u00edjmech'], 'fleeting e (p\u0159\u00edjem\u2192p\u0159\u00edjm-)'),
        ('pron\u00e1jem', ['pron\u00e1jem','pron\u00e1jmu','pron\u00e1jmem','pron\u00e1jmy','pron\u00e1jm\u016f','pron\u00e1jm\u016fm','pron\u00e1jmech'], 'fleeting e (pron\u00e1jem\u2192pron\u00e1jm-)'),
        ('n\u00e1jem', ['n\u00e1jem','n\u00e1jmu','n\u00e1jmem','n\u00e1jmy','n\u00e1jm\u016f'], 'fleeting e (n\u00e1jem\u2192n\u00e1jm-)'),
        ('z\u00e1jem', ['z\u00e1jem','z\u00e1jmu','z\u00e1jmem','z\u00e1jmy','z\u00e1jm\u016f','z\u00e1jm\u016fm','z\u00e1jmech'], 'fleeting e (z\u00e1jem\u2192z\u00e1jm-)'),
        ('n\u00e1zev', ['n\u00e1zev','n\u00e1zvu','n\u00e1zvem','n\u00e1zvy','n\u00e1zv\u016f','n\u00e1zv\u016fm','n\u00e1zvech'], 'fleeting e (n\u00e1zev\u2192n\u00e1zv-)'),
        ('v\u00fdpo\u010det', ['v\u00fdpo\u010det','v\u00fdpo\u010dtu','v\u00fdpo\u010dtem','v\u00fdpo\u010dty','v\u00fdpo\u010dt\u016f'], 'fleeting e (v\u00fdpo\u010det\u2192v\u00fdpo\u010dt-)'),
        ('stupe\u0148', ['stupe\u0148','stupn\u011b','stupni','stupn\u011bm','stup\u0148\u016f','stup\u0148\u016fm','stup\u0148\u00edch'], 'fleeting e (stupe\u0148\u2192stup\u0148-)'),
        ('poh\u0159eb', ['poh\u0159eb','poh\u0159bu','poh\u0159bem','poh\u0159by','poh\u0159b\u016f','poh\u0159b\u016fm','poh\u0159bech'], 'fleeting e (poh\u0159eb\u2192poh\u0159b-)'),
        ('povode\u0148', ['povode\u0148','povodn\u011b','povodni','povodn\u00ed','povodn\u00edm','povodn\u00edch','povodn\u011bmi'], 'fleeting e (povode\u0148\u2192povodn-)'),
        ('\u00farove\u0148', ['\u00farove\u0148','\u00farovn\u011b','\u00farovni','\u00farovn\u00ed','\u00farovn\u00edm','\u00farovn\u00edch','\u00farovn\u011bmi'], 'fleeting e (\u00farove\u0148\u2192\u00farovn-)'),

        # === Suppletive / highly irregular ===
        ('d\u00edt\u011b', ['d\u00edt\u011b','d\u00edt\u011bte','d\u00edt\u011bti','d\u011bti','d\u011bt\u00ed','d\u011btem','d\u011btmi','d\u011btech'], 'suppletive (d\u00edt\u011b\u2192d\u011bti)'),
        ('\u010dlov\u011bk', ['\u010dlov\u011bk','\u010dlov\u011bka','\u010dlov\u011bku','\u010dlov\u011bkem','\u010dlov\u011b\u010de','lid\u00e9','lid\u00ed','lidem','lidmi','lidech'], 'suppletive (\u010dlov\u011bk\u2192lid\u00e9)'),
        ('rok', ['rok','roku','roce','rokem','roky','rok\u016f','rok\u016fm','roc\u00edch','let','letech','l\u00e9ta','lety'], 'suppletive plural (let/letech)'),
        ('oko', ['oko','oka','oku','okem','o\u010di','o\u010d\u00ed','o\u010d\u00edm','o\u010dima','o\u010d\u00edch'], 'irregular plural (oko\u2192o\u010di)'),

        # === Stem alternation: \u00ed \u2192 \u011b ===
        ('v\u00edtr', ['v\u00edtr','v\u011btru','v\u011btrem','v\u011bt\u0159e','v\u011btry','v\u011btr\u016f','v\u011btr\u016fm','v\u011btrech'], '\u00ed\u2192\u011b (v\u00edtr\u2192v\u011btr-)'),

        # === Regular but all bare (insurance domain nouns) ===
        ('n\u00e1rok', ['n\u00e1rok','n\u00e1roku','n\u00e1rokem','n\u00e1roky','n\u00e1rok\u016f','n\u00e1rok\u016fm','n\u00e1roc\u00edch'], 'regular but all bare'),
        ('vznik', ['vznik','vzniku','vznikem','vzniky','vznik\u016f'], 'regular but all bare'),
        ('z\u00e1nik', ['z\u00e1nik','z\u00e1niku','z\u00e1nikem','z\u00e1niky','z\u00e1nik\u016fm'], 'regular but all bare'),
        ('\u00fanik', ['\u00fanik','\u00faniku','\u00fanikem','\u00faniky','\u00fanik\u016f'], 'regular but all bare'),
        ('z\u00e1krok', ['z\u00e1krok','z\u00e1kroku','z\u00e1krokem','z\u00e1kroky','z\u00e1krok\u016f','z\u00e1krok\u016fm','z\u00e1kroc\u00edch'], 'k\u2192c in loc.pl.'),
        ('v\u00fdpov\u011b\u010f', ['v\u00fdpov\u011b\u010f','v\u00fdpov\u011bdi','v\u00fdpov\u011bd\u00ed','v\u00fdpov\u011bd\u00edm','v\u00fdpov\u011bd\u00edch','v\u00fdpov\u011b\u010fmi'], 'regular but all bare'),

        # === -n\u00edk nouns (animate, k\u2192c in plural) ===
        ('pojistn\u00edk', ['pojistn\u00edk','pojistn\u00edka','pojistn\u00edkem','pojistn\u00edkovi','pojistn\u00edky','pojistn\u00edk\u016f','pojistn\u00edk\u016fm','pojistn\u00edci'], '-n\u00edk animate noun'),
        ('vlastn\u00edk', ['vlastn\u00edk','vlastn\u00edka','vlastn\u00edkem','vlastn\u00edkovi','vlastn\u00edky','vlastn\u00edk\u016f','vlastn\u00edk\u016fm','vlastn\u00edci'], '-n\u00edk animate noun'),
        ('\u00fa\u010dastn\u00edk', ['\u00fa\u010dastn\u00edk','\u00fa\u010dastn\u00edka','\u00fa\u010dastn\u00edkem','\u00fa\u010dastn\u00edku','\u00fa\u010dastn\u00edkovi','\u00fa\u010dastn\u00edky','\u00fa\u010dastn\u00edk\u016f','\u00fa\u010dastn\u00edk\u016fm','\u00fa\u010dastn\u00edci','\u00fa\u010dastn\u00edch'], '-n\u00edk animate noun'),
        ('z\u00e1kon\u00edk', ['z\u00e1kon\u00edk','z\u00e1kon\u00edku','z\u00e1kon\u00edkem','z\u00e1kon\u00edky','z\u00e1kon\u00edk\u016f'], '-n\u00edk inanimate noun'),
        ('sazebn\u00edk', ['sazebn\u00edk','sazebn\u00edku','sazebn\u00edkem','sazebn\u00edky','sazebn\u00edk\u016f'], '-n\u00edk inanimate noun'),

        # === More insurance-relevant nouns ===
        ('\u00fa\u010del', ['\u00fa\u010del','\u00fa\u010delu','\u00fa\u010delem','\u00fa\u010dely','\u00fa\u010del\u016f','\u00fa\u010del\u016fm'], 'regular but all bare'),
        ('doklad', ['doklad','dokladu','dokladem','doklady','doklad\u016f','doklad\u016fm','dokladech'], 'regular but all bare'),
        ('p\u0159\u00edpad', ['p\u0159\u00edpad','p\u0159\u00edpadu','p\u0159\u00edpadem','p\u0159\u00edpady','p\u0159\u00edpad\u016f','p\u0159\u00edpad\u016fm','p\u0159\u00edpadech'], 'regular but all bare'),
        ('n\u00e1sledek', ['n\u00e1sledek','n\u00e1sledku','n\u00e1sledkem','n\u00e1sledky','n\u00e1sledk\u016f'], 'fleeting e (n\u00e1sledek\u2192n\u00e1sledk-)'),
        ('prost\u0159edek', ['prost\u0159edek','prost\u0159edku','prost\u0159edkem','prost\u0159edky','prost\u0159edk\u016f'], 'fleeting e (prost\u0159edek\u2192prost\u0159edk-)'),
    ]

    print("\n" + "="*70)
    print("IRREGULAR NOUN GROUPS FOUND IN BARE WORDS FROM REPORT")
    print("="*70)

    found_groups = []
    total_bare_covered = 0

    for base, forms, pattern in groups:
        in_report = [f for f in forms if f in bare_words]
        in_dict = [f for f in forms if f in dict_bare]
        if in_report:
            found_groups.append((base, in_report, in_dict, pattern))

    # Sort by number of forms found in report (descending)
    found_groups.sort(key=lambda x: len(x[1]), reverse=True)

    for base, in_report, in_dict, pattern in found_groups:
        total_bare_covered += len(in_report)
        extra = [f for f in in_dict if f not in in_report]
        print(f"\n  {base} ({pattern})")
        print(f"    In report ({len(in_report)}): {', '.join(in_report)}")
        if extra:
            shown = extra[:10]
            print(f"    Also in dict bare ({len(extra)}): {', '.join(shown)}{'...' if len(extra)>10 else ''}")

    print(f"\n{'='*70}")
    print(f"Total groups found: {len(found_groups)}")
    print(f"Bare forms covered from report: {total_bare_covered} of {len(bare_words)}")

    # Auto-detect common patterns in remaining bare words
    print(f"\n{'='*70}")
    print("BARE WORDS BY SUFFIX PATTERN")
    print("="*70)

    suffix_patterns = [
        ('-n\u011b (adverbs)', lambda w: w.endswith('n\u011b')),
        ('-icky (adverbs)', lambda w: w.endswith('icky')),
        ('-ov\u011b (adverbs)', lambda w: w.endswith('ov\u011b')),
        ('-\u0161t\u011b (locative)', lambda w: w.endswith('\u0161t\u011b')),
        ('-\u00e1ch (loc.pl.)', lambda w: w.endswith('\u00e1ch')),
        ('-ech (loc.pl.)', lambda w: w.endswith('ech')),
        ('-\u016fm (dat.pl.)', lambda w: w.endswith('\u016fm')),
        ('-\u016f (gen.pl.)', lambda w: w.endswith('\u016f') and not w.endswith('\u016fm')),
        ('-em (instr.sg.)', lambda w: w.endswith('em')),
        ('-ek (diminutive)', lambda w: w.endswith('ek')),
        ('-n\u00edk/-n\u00edk', lambda w: 'n\u00edk' in w),
    ]

    for label, pred in suffix_patterns:
        words = sorted([w for w in bare_words if pred(w)])
        if words:
            shown = words[:20]
            print(f"\n  {label} ({len(words)}): {', '.join(shown)}{'...' if len(words)>20 else ''}")

    # Summary: what could be done about it
    print(f"\n{'='*70}")
    print("RECOMMENDATION FOR SEARCH USE CASE")
    print("="*70)
    print("""
For search (e.g. 'pojisteni dum' should find 'pojisteni domu'), you need
these irregular forms to map to the same stem. Options:

1. SYNONYM MAP (best for search): Create a synonym/alias file that maps
   irregular forms to a canonical form:
     dum,domu,dome,domem,domy,domech -> dum
     dite,ditete,deti,detmi,detech -> dite

2. CUSTOM AFFIX RULES: Add new affix flags specifically for irregular
   nouns (e.g., flag I for irregular). This requires modifying the .aff file.

3. MANUAL DICTIONARY ENTRIES: Add the base form with a custom flag that
   generates all oblique forms via affix rules (but this doesn't work for
   stem-changing words without custom rules).

Option 1 (synonym map) is the most practical for search engines like Solr/
Elasticsearch. Option 2 is the proper hunspell solution but more complex.
""")

if __name__ == '__main__':
    main()
