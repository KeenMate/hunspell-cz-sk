#!/usr/bin/env python3
"""
Tag Irregular Nouns — Post-fixer pass for stem-changing patterns.

Applies curated flag assignments for irregular noun patterns (R/J/Q/T/U)
and scans for additional candidates matching these patterns. Removes
redundant bare inflected forms that become regenerable via the new flags.

Usage:
    python tag_irregular_nouns.py [--dict cs_cz_fixed.dict] [--affix cs_cz.affix] \
        [-o cs_cz_final.dict] [--changelog changelog_tags.txt] [-v]
"""

import argparse
import os
import re
import sys
from collections import defaultdict

from hunspell_checker import (
    parse_affix_file,
    parse_dict_file,
    apply_suffix_rule,
    expand_dictionary,
)

# ---------------------------------------------------------------------------
# Curated word → flag assignments (known stem-changing words)
# ---------------------------------------------------------------------------

CURATED_TAGS = {
    # R flag: ů→o vowel alternation
    "dům": "R",
    "dvůr": "R",
    "kůň": "R",
    "stůl": "R",
    "důl": "R",
    "vůl": "R",

    # J flag: fleeting-e masculine nouns
    # -em ending
    "příjem": "J", "pronájem": "J", "zájem": "J", "pojem": "J", "nájem": "J",
    # -et ending
    "účet": "J", "výpočet": "J", "rozpočet": "J",
    # -ev ending
    "název": "J",
    # -eb ending
    "pohřeb": "J",
    # -eň ending (masculine)
    "stupeň": "J",
    # -en ending
    "den": "J", "týden": "J",

    # Q flag: fleeting-e feminine nouns (-eň)
    "povodeň": "Q",
    "úroveň": "Q",
}


# ---------------------------------------------------------------------------
# Scanning for additional candidates
# ---------------------------------------------------------------------------

def scan_nik_candidates(entries, min_forms=3, verbose=False):
    """Scan for -ník words that should get T flag (animate, k→c in pl1)."""
    bare = set()
    base_lookup = {}
    for word, flags, pos in entries:
        base_lookup[word] = (flags, pos)
        if not flags:
            bare.add(word)

    candidates = {}
    for word, (flags, pos) in base_lookup.items():
        if not word.endswith("ník"):
            continue
        if "T" in flags:
            continue

        expected_forms = [
            word + "a", word + "ovi", word + "u", word + "em",
            word[:-1] + "ci",  # k→c in pl1
            word + "y", word + "ů", word + "ům", word + "ech",
        ]
        existing = [f for f in expected_forms if f in bare]

        # Lower threshold if already flagged with B (we mainly want k→ci)
        threshold = 1 if "B" in flags else min_forms

        if len(existing) >= threshold:
            candidates[word] = set(existing)
            if verbose:
                print(f"    T candidate: {word} ({len(existing)} bare forms: "
                      f"{', '.join(sorted(existing)[:5])})", file=sys.stderr)

    return candidates


def scan_k_candidates(entries, min_forms=3, verbose=False):
    """Scan for bare inanimate -k words (not -ek, not -ník) that should get U flag."""
    bare = set()
    for word, flags, pos in entries:
        if not flags:
            bare.add(word)

    candidates = {}
    for word in bare:
        if not word.endswith("k"):
            continue
        if word.endswith("ek") or word.endswith("ník"):
            continue

        expected_forms = [
            word + "u", word + "e", word + "em",
            word + "y", word + "ů", word + "ům",
            word[:-1] + "cích",  # k→c in loc.pl
        ]
        existing = [f for f in expected_forms if f in bare]

        if len(existing) >= min_forms:
            candidates[word] = set(existing)
            if verbose:
                print(f"    U candidate: {word} ({len(existing)} bare forms: "
                      f"{', '.join(sorted(existing)[:5])})", file=sys.stderr)

    return candidates


# ---------------------------------------------------------------------------
# Form generation
# ---------------------------------------------------------------------------

def compute_generated_forms(base, flag, suffixes):
    """Forward-apply all suffix rules for flag to base. Returns set of forms."""
    forms = set()
    if flag not in suffixes:
        return forms
    for strip, add, condition, _cross in suffixes[flag]:
        form = apply_suffix_rule(base, strip, add, condition)
        if form is not None and form != base:
            forms.add(form)
    return forms


# ---------------------------------------------------------------------------
# Dictionary processing
# ---------------------------------------------------------------------------

def process_dictionary(dict_path, output_path, tags_to_apply, forms_to_remove,
                       verbose=False):
    """Read dictionary, apply tag changes and remove redundant bare forms."""
    stats = defaultdict(int)
    changes = []
    output_lines = []
    first_line = True

    with open(dict_path, encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip("\n").rstrip("\r")
            stats["lines_read"] += 1

            if first_line:
                first_line = False
                if raw.strip().isdigit():
                    output_lines.append(None)  # placeholder for count
                    continue

            if not raw.strip():
                output_lines.append(raw)
                continue

            # Parse line
            work = raw.strip()
            pos = ""
            pos_match = re.search(r"\bpo:(\S+)", work)
            if pos_match:
                pos = pos_match.group(1)
                work = work[:pos_match.start()].strip()
            work = re.sub(r"\bis:\S+", "", work).strip()

            if "/" in work:
                word_orig, flags_str = work.split("/", 1)
                word_orig = word_orig.strip()
                flags_str = flags_str.strip()
            else:
                word_orig = work
                flags_str = ""

            word_lower = word_orig.lower()
            is_bare = not flags_str

            # Should this word get a new flag?
            if word_lower in tags_to_apply:
                new_flag = tags_to_apply[word_lower]
                if new_flag not in flags_str:
                    # For -ník words: replace B with T (T is superset of B)
                    if new_flag == "T" and "B" in flags_str:
                        merged = flags_str.replace("B", "T")
                    else:
                        merged = flags_str + new_flag if flags_str else new_flag
                    final_pos = pos if pos else "noun"
                    new_line = f"{word_orig}/{merged} po:{final_pos}"
                    output_lines.append(new_line)
                    stats["tags_added"] += 1
                    changes.append(("TAG", f"{raw.strip()} -> {new_line}"))
                    continue

            # Should this bare form be removed?
            if is_bare and word_lower in forms_to_remove:
                base, flag = forms_to_remove[word_lower]
                stats["forms_removed"] += 1
                changes.append(("REMOVE_FORM",
                                f"{word_orig} (covered by {base}/{flag})"))
                continue

            # Pass through unchanged
            output_lines.append(raw)
            stats["unchanged"] += 1

    # Update entry count
    entry_count = sum(1 for l in output_lines if l is not None and l.strip())
    if output_lines and output_lines[0] is None:
        output_lines[0] = str(entry_count)

    with open(output_path, "w", encoding="utf-8") as f:
        for line in output_lines:
            if line is not None:
                f.write(line + "\n")

    stats["lines_written"] = sum(1 for l in output_lines if l is not None)
    return dict(stats), changes


# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------

def write_changelog(path, stats, changes, missing, validation_stats):
    """Write changelog for tagging pass."""
    lines = []
    lines.append("=" * 70)
    lines.append("IRREGULAR NOUN TAGGER — CHANGELOG")
    lines.append("=" * 70)
    lines.append("")

    lines.append("SUMMARY")
    lines.append("-" * 70)
    for key in ["lines_read", "lines_written", "tags_added",
                 "forms_removed", "unchanged"]:
        lines.append(f"  {key:30s} {stats.get(key, 0)}")
    lines.append("")

    if validation_stats:
        total_forms, new_bare, new_entries = validation_stats
        lines.append("VALIDATION")
        lines.append("-" * 70)
        lines.append(f"  New dictionary entries:     {new_entries}")
        lines.append(f"  Expanded forms:             {total_forms}")
        lines.append(f"  Remaining bare entries:     {new_bare}")
        if missing:
            lines.append(f"  WARNING: {len(missing)} removed forms NOT regenerated:")
            for f in sorted(missing)[:100]:
                lines.append(f"    {f}")
            if len(missing) > 100:
                lines.append(f"    ... and {len(missing) - 100} more")
        else:
            lines.append("  All removed forms verified regenerated.")
        lines.append("")

    for action in ["TAG", "REMOVE_FORM"]:
        items = [detail for a, detail in changes if a == action]
        if items:
            lines.append(f"{action} ({len(items)})")
            lines.append("-" * 70)
            for item in sorted(items):
                lines.append(f"  {item}")
            lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Tag irregular nouns with stem-changing affix flags "
                    "(R/J/Q/T/U).",
    )
    parser.add_argument("--dict", default="cs_cz_fixed.dict",
                        help="Input dictionary (default: cs_cz_fixed.dict)")
    parser.add_argument("--affix", default="cs_cz.affix",
                        help="Affix file (default: cs_cz.affix)")
    parser.add_argument("-o", "--output", default="cs_cz_final.dict",
                        help="Output dictionary (default: cs_cz_final.dict)")
    parser.add_argument("--changelog", default="changelog_tags.txt",
                        help="Changelog output (default: changelog_tags.txt)")
    parser.add_argument("--min-forms", type=int, default=3,
                        help="Min bare forms for scan candidates (default: 3)")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = (args.dict if os.path.isabs(args.dict)
                 else os.path.join(script_dir, args.dict))
    affix_path = (args.affix if os.path.isabs(args.affix)
                  else os.path.join(script_dir, args.affix))
    output_path = (args.output if os.path.isabs(args.output)
                   else os.path.join(script_dir, args.output))
    changelog_path = (args.changelog if os.path.isabs(args.changelog)
                      else os.path.join(script_dir, args.changelog))

    for path, label in [(dict_path, "Dictionary"), (affix_path, "Affix")]:
        if not os.path.exists(path):
            print(f"Error: {label} file not found: {path}", file=sys.stderr)
            sys.exit(1)

    # ---- Step 1: Parse ----
    print("Step 1: Parsing affix rules and dictionary...", file=sys.stderr)
    prefixes, suffixes = parse_affix_file(affix_path)
    entries = parse_dict_file(dict_path)

    bare = set()
    base_lookup = {}
    for word, flags, pos in entries:
        base_lookup[word] = (flags, pos)
        if not flags:
            bare.add(word)

    print(f"  {len(entries)} entries ({len(bare)} bare)", file=sys.stderr)

    # ---- Step 2: Curated tags ----
    print("Step 2: Applying curated tag assignments...", file=sys.stderr)
    tags_to_apply = {}

    for word, flag in CURATED_TAGS.items():
        if word in base_lookup:
            existing_flags = base_lookup[word][0]
            if flag not in existing_flags:
                tags_to_apply[word] = flag
                if args.verbose:
                    print(f"  Curated: {word} -> /{flag}", file=sys.stderr)
        elif args.verbose:
            print(f"  Curated word not in dict: {word}", file=sys.stderr)

    print(f"  {len(tags_to_apply)} curated tags to apply", file=sys.stderr)

    # ---- Step 3: Scan -ník candidates (T flag) ----
    print("Step 3: Scanning for -ník candidates (T flag)...", file=sys.stderr)
    nik_candidates = scan_nik_candidates(
        entries, min_forms=args.min_forms, verbose=args.verbose,
    )
    for word in nik_candidates:
        if word not in tags_to_apply:
            tags_to_apply[word] = "T"
    print(f"  {len(nik_candidates)} -ník candidates found", file=sys.stderr)

    # ---- Step 4: Scan inanimate -k candidates (U flag) ----
    print("Step 4: Scanning for inanimate -k candidates (U flag)...",
          file=sys.stderr)
    k_candidates = scan_k_candidates(
        entries, min_forms=args.min_forms, verbose=args.verbose,
    )
    for word in k_candidates:
        if word not in tags_to_apply:
            tags_to_apply[word] = "U"
    print(f"  {len(k_candidates)} inanimate -k candidates found",
          file=sys.stderr)

    # ---- Step 5: Compute forms to remove ----
    print("Step 5: Computing forms to remove...", file=sys.stderr)
    forms_to_remove = {}
    for word, flag in tags_to_apply.items():
        generated = compute_generated_forms(word, flag, suffixes)
        for form in generated:
            if form in bare and form not in tags_to_apply:
                forms_to_remove[form] = (word, flag)

    print(f"  {len(tags_to_apply)} bases will be tagged", file=sys.stderr)
    print(f"  {len(forms_to_remove)} bare forms will be removed",
          file=sys.stderr)

    # ---- Step 6: Process dictionary ----
    print(f"Step 6: Writing tagged dictionary to {output_path}...",
          file=sys.stderr)
    stats, changes = process_dictionary(
        dict_path, output_path, tags_to_apply, forms_to_remove,
        verbose=args.verbose,
    )

    # ---- Step 7: Validate ----
    print("Step 7: Validating output...", file=sys.stderr)
    val_entries = parse_dict_file(output_path)
    val_prefixes, val_suffixes = parse_affix_file(affix_path)
    form_lookup, val_bare, val_base = expand_dictionary(
        val_entries, val_prefixes, val_suffixes, verbose=args.verbose,
    )

    missing = set()
    for form in forms_to_remove:
        if form not in form_lookup:
            missing.add(form)
        else:
            flagged = [e for e in form_lookup[form] if e[1]]
            if not flagged:
                missing.add(form)

    if missing:
        print(f"  WARNING: {len(missing)} forms removed but NOT regenerated!",
              file=sys.stderr)
        if args.verbose:
            for f in sorted(missing)[:20]:
                print(f"    {f}", file=sys.stderr)
            if len(missing) > 20:
                print(f"    ... and {len(missing) - 20} more", file=sys.stderr)
    else:
        print(f"  All {len(forms_to_remove)} removed forms verified "
              f"regenerated.", file=sys.stderr)

    print(f"  Tagged dictionary: {len(val_base)} entries, "
          f"{len(form_lookup)} expanded forms, {len(val_bare)} bare",
          file=sys.stderr)

    # ---- Step 8: Changelog ----
    print(f"Step 8: Writing changelog to {changelog_path}...", file=sys.stderr)
    write_changelog(
        changelog_path, stats, changes, missing,
        (len(form_lookup), len(val_bare), len(val_base)),
    )

    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
