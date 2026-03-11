#!/usr/bin/env python3
"""
Hunspell Dictionary Fixer — Dictionary-Wide Consolidation & Repair.

Analyzes the Czech hunspell dictionary to find bare entries (without affix flags)
that can be consolidated into flagged entries, removes verb duplicates, and
produces a corrected dictionary with a changelog.

Usage:
    python hunspell_fixer.py [--dict cs_cz.dict] [--affix cs_cz.affix] \
        [-o cs_cz_fixed.dict] [--changelog changelog.txt] [--min-group 3] [-v] [--dry-run]
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
# Constants
# ---------------------------------------------------------------------------

# These are set dynamically from LangConfig in main()
CONSOLIDATION_FLAGS = []
FLAG_PRIORITY = {}
FLAG_POS = {}


# ---------------------------------------------------------------------------
# 1. Reverse Morphology
# ---------------------------------------------------------------------------

def reverse_morphology_all(bare_words_set, suffixes, base_lookup, verbose=False):
    """For every bare entry, reverse every suffix rule to find candidate (base, flag) groups.

    Returns:
        groups: defaultdict((candidate_base, flag) -> set of bare forms explained)
    """
    groups = defaultdict(set)
    checked = 0

    for word in bare_words_set:
        for flag in CONSOLIDATION_FLAGS:
            if flag not in suffixes:
                continue
            for strip, add, condition, _cross in suffixes[flag]:
                if not add:
                    # Rule adds nothing — can't reverse (endswith("") is always True)
                    continue
                if not word.endswith(add):
                    continue

                # Reverse: remove suffix addition, restore stripped part
                candidate = word[: -len(add)] + strip
                if not candidate:
                    continue

                # Verify condition on candidate (same check the forward rule uses)
                if condition != ".":
                    if not re.search(condition + "$", candidate):
                        continue

                # Candidate base must exist somewhere in the dictionary
                if candidate in base_lookup:
                    groups[(candidate, flag)].add(word)

        checked += 1
        if verbose and checked % 50000 == 0:
            print(f"    ... {checked}/{len(bare_words_set)} bare words processed", file=sys.stderr)

    if verbose:
        print(f"  Found {len(groups)} candidate (base, flag) groups", file=sys.stderr)
    return groups


# ---------------------------------------------------------------------------
# 2. Forward Validation
# ---------------------------------------------------------------------------

def forward_validate(base, flag, suffixes, bare_words_set):
    """Forward-apply all suffix rules for *flag* to *base*.

    Returns:
        validated: set of bare forms actually generated (excluding the base itself)
        applicable: number of rules whose condition/strip matched the base
    """
    validated = set()
    applicable = 0

    if flag not in suffixes:
        return validated, applicable

    for strip, add, condition, _cross in suffixes[flag]:
        form = apply_suffix_rule(base, strip, add, condition)
        if form is not None:
            applicable += 1
            # Only count forms that are distinct from the base and currently bare
            if form != base and form in bare_words_set:
                validated.add(form)

    return validated, applicable


# ---------------------------------------------------------------------------
# 3. Consolidation Selection (scoring + greedy conflict resolution)
# ---------------------------------------------------------------------------

def select_consolidations(groups, suffixes, bare_words_set, base_lookup,
                          min_group=3, min_coverage=0.6, verbose=False):
    """Score, filter, and resolve conflicts among consolidation groups.

    Returns:
        accepted: list of group dicts {base, flag, forms, score, applicable}
        assigned_forms: dict mapping each bare form -> (base, flag)
    """
    # --- Score every candidate group ---
    scored = []
    for (base, flag), reverse_forms in groups.items():
        # Quick pre-filter on reverse-matched count
        if len(reverse_forms) < min_group:
            continue

        # Forward validation determines the TRUE set of bare forms this base+flag covers
        validated, applicable = forward_validate(base, flag, suffixes, bare_words_set)

        if len(validated) < min_group:
            continue

        # Coverage filter: fraction of applicable rules that produce existing bare forms
        if applicable > 0 and len(validated) / applicable < min_coverage:
            continue

        scored.append({
            "base": base,
            "flag": flag,
            "forms": validated,
            "score": len(validated),
            "applicable": applicable,
        })

    # Sort: highest score first, then by flag priority
    scored.sort(key=lambda g: (-g["score"], -FLAG_PRIORITY.get(g["flag"], 0)))

    if verbose:
        print(f"  {len(scored)} groups pass validation & coverage filter", file=sys.stderr)

    # --- Greedy conflict resolution ---
    assigned_forms = {}  # form -> (base, flag)
    used_bases = {}      # base -> flag (a base can only serve one flag)
    accepted = []

    for group in scored:
        base = group["base"]
        flag = group["flag"]

        # Base must not already be claimed as someone else's form
        if base in assigned_forms:
            continue
        # Base must not already be used for a *different* flag
        if base in used_bases and used_bases[base] != flag:
            continue

        # Keep only forms not yet claimed
        available = {f for f in group["forms"] if f not in assigned_forms}
        if len(available) < min_group:
            continue

        # Commit
        for f in available:
            assigned_forms[f] = (base, flag)
        used_bases[base] = flag

        group["forms"] = available
        group["score"] = len(available)
        accepted.append(group)

    if verbose:
        total = sum(g["score"] for g in accepted)
        print(f"  Accepted {len(accepted)} groups covering {total} forms", file=sys.stderr)

    return accepted, assigned_forms


# ---------------------------------------------------------------------------
# 4. Verb Duplicate Detection
# ---------------------------------------------------------------------------

def find_verb_duplicates(entries, verb_flags=None, verb_pos="verb", verbose=False):
    """Find bare entries whose word also appears as a flagged verb.

    Returns:
        set of words to remove (the bare duplicate).
    """
    if verb_flags is None:
        verb_flags = {"N"}
    verbs = set()
    bare = set()
    for word, flags, pos in entries:
        if any(f in flags for f in verb_flags) and pos == verb_pos:
            verbs.add(word)
        elif not flags:
            bare.add(word)

    dupes = bare & verbs
    if verbose:
        print(f"  Found {len(dupes)} verb duplicates", file=sys.stderr)
    return dupes


# ---------------------------------------------------------------------------
# 5. Dictionary Processing (line-by-line rewrite)
# ---------------------------------------------------------------------------

def _parse_line(raw_line):
    """Parse a single dictionary line.

    Returns (word_lower, flags_str, pos, word_original) or (None, ...) for blank lines.
    """
    work = raw_line.strip()
    if not work:
        return None, "", "", ""

    # Extract POS tag
    pos = ""
    pos_match = re.search(r"\bpo:(\S+)", work)
    if pos_match:
        pos = pos_match.group(1)
        work = work[: pos_match.start()].strip()

    # Strip morphological is: tags
    work = re.sub(r"\bis:\S+", "", work).strip()

    # Split word/flags
    if "/" in work:
        word_part, flags_str = work.split("/", 1)
        flags_str = flags_str.strip()
    else:
        word_part = work
        flags_str = ""

    return word_part.strip().lower(), flags_str, pos, word_part.strip()


def process_dictionary(dict_path, output_path, consolidations, assigned_forms,
                       verb_duplicates, verbose=False):
    """Read the original dictionary, apply all changes, write the fixed version.

    Returns:
        stats: dict of counters
        changes: list of (action_type, detail_string) for the changelog
    """
    # Build fast lookups
    base_to_consol = {}
    for group in consolidations:
        base_to_consol[group["base"]] = (group["flag"], FLAG_POS.get(group["flag"], ""))

    forms_to_remove = set(assigned_forms.keys())

    stats = defaultdict(int)
    changes = []
    output_lines = []
    first_line = True

    with open(dict_path, encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip("\n").rstrip("\r")
            stats["lines_read"] += 1

            # Handle the very first line (entry count)
            if first_line:
                first_line = False
                if raw.strip().isdigit():
                    output_lines.append(None)  # placeholder — filled at the end
                    continue

            if not raw.strip():
                output_lines.append(raw)
                continue

            word_lower, flags_str, pos, word_orig = _parse_line(raw)
            if word_lower is None:
                output_lines.append(raw)
                continue

            is_bare = not flags_str

            # ------ Bare-entry decisions ------
            if is_bare:
                # (a) Is this word a consolidation base?
                if word_lower in base_to_consol:
                    new_flag, new_pos = base_to_consol[word_lower]
                    final_pos = pos if pos else new_pos
                    new_line = f"{word_orig}/{new_flag} po:{final_pos}"
                    output_lines.append(new_line)
                    stats["bases_flagged"] += 1
                    changes.append(("CONSOLIDATE_BASE", f"{word_orig} -> {new_line}"))
                    continue

                # (b) Is this word a form covered by a consolidation?
                if word_lower in forms_to_remove:
                    base, flag = assigned_forms[word_lower]
                    stats["forms_removed"] += 1
                    changes.append(("REMOVE_FORM", f"{word_orig} (covered by {base}/{flag})"))
                    continue

                # (c) Is this a verb duplicate?
                if word_lower in verb_duplicates:
                    stats["verb_dupes_removed"] += 1
                    changes.append(("REMOVE_VERB_DUPE", f"{word_orig} (duplicate of /N po:verb)"))
                    continue

            # ------ Flagged-entry decisions ------
            else:
                # Is this a flagged entry that is also a consolidation base? → add flag
                if word_lower in base_to_consol:
                    new_flag, new_pos = base_to_consol[word_lower]
                    if new_flag not in flags_str:
                        merged_flags = flags_str + new_flag
                        final_pos = pos if pos else new_pos
                        new_line = f"{word_orig}/{merged_flags} po:{final_pos}"
                        output_lines.append(new_line)
                        stats["bases_flag_added"] += 1
                        changes.append(("ADD_FLAG", f"{raw.strip()} -> {new_line}"))
                        continue

            # ------ Default: pass through unchanged ------
            output_lines.append(raw)
            stats["unchanged"] += 1

    # Compute new entry count (non-empty, non-placeholder lines)
    entry_count = sum(1 for l in output_lines if l is not None and l.strip())
    if output_lines and output_lines[0] is None:
        output_lines[0] = str(entry_count)

    # Write
    with open(output_path, "w", encoding="utf-8") as f:
        for line in output_lines:
            if line is not None:
                f.write(line + "\n")

    stats["lines_written"] = sum(1 for l in output_lines if l is not None)
    return dict(stats), changes


# ---------------------------------------------------------------------------
# 6. Validation Pass
# ---------------------------------------------------------------------------

def validate_output(output_path, affix_path, removed_forms, verbose=False):
    """Expand the fixed dictionary and verify every removed form is regenerated.

    Returns:
        missing: set of forms removed but NOT regenerated via affix expansion
        total_forms: number of expanded forms in the new dictionary
        new_bare_count: number of remaining bare entries
        new_entry_count: number of entries in the new dictionary
    """
    if verbose:
        print("  Expanding fixed dictionary for validation...", file=sys.stderr)

    entries = parse_dict_file(output_path)
    prefixes, suffixes = parse_affix_file(affix_path)
    form_lookup, bare_words, base_lookup = expand_dictionary(
        entries, prefixes, suffixes, verbose=verbose
    )

    missing = set()
    for form in removed_forms:
        if form not in form_lookup:
            missing.add(form)
        else:
            # Must come from a flagged expansion (not bare-only)
            flagged = [e for e in form_lookup[form] if e[1]]
            if not flagged:
                missing.add(form)

    return missing, len(form_lookup), len(bare_words), len(base_lookup)


# ---------------------------------------------------------------------------
# 7. Changelog
# ---------------------------------------------------------------------------

def write_changelog(path, stats, changes, missing, validation_stats):
    """Write a human-readable changelog summarising all changes."""
    lines = []
    lines.append("=" * 70)
    lines.append("HUNSPELL DICTIONARY FIXER — CHANGELOG")
    lines.append("=" * 70)
    lines.append("")

    # --- Summary table ---
    lines.append("SUMMARY")
    lines.append("-" * 70)
    for key in [
        "lines_read", "lines_written", "bases_flagged", "bases_flag_added",
        "forms_removed", "verb_dupes_removed", "unchanged",
    ]:
        lines.append(f"  {key:30s} {stats.get(key, 0)}")
    removed = stats.get("forms_removed", 0) + stats.get("verb_dupes_removed", 0)
    lines.append(f"  {'net_entries_removed':30s} {removed}")
    lines.append("")

    # --- Validation ---
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

    # --- Detailed change lists ---
    for action in ["CONSOLIDATE_BASE", "ADD_FLAG", "REMOVE_FORM", "REMOVE_VERB_DUPE"]:
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
# 8. CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Hunspell Dictionary Fixer — consolidate bare entries into "
                    "flagged entries and remove duplicates.",
    )
    parser.add_argument(
        "--dict", help="Path to hunspell .dict file (default: auto from --lang)",
    )
    parser.add_argument(
        "--affix", help="Path to hunspell .affix file (default: auto from --lang)",
    )
    parser.add_argument(
        "-o", "--output", help="Output dictionary path (default: auto from --lang)",
    )
    parser.add_argument(
        "--changelog", default="changelog.txt",
        help="Changelog output path (default: changelog.txt)",
    )
    parser.add_argument(
        "--lang", help="Language code (cs/sk). Auto-detected from affix file if not set.",
    )
    parser.add_argument(
        "--min-group", type=int, default=3,
        help="Minimum forms required to accept a consolidation group (default: 3)",
    )
    parser.add_argument(
        "--min-coverage", type=float, default=0.6,
        help="Minimum fraction of applicable rules with matching bare forms (default: 0.6)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Analyze only — do not write output files",
    )

    args = parser.parse_args()

    from lang_config import LangConfig, detect_language

    # Resolve paths relative to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Determine language for defaults
    lang_hint = args.lang
    if not lang_hint and args.affix:
        affix_test = args.affix if os.path.isabs(args.affix) else os.path.join(script_dir, args.affix)
        if os.path.exists(affix_test):
            lang_hint = detect_language(affix_test)

    if lang_hint == "sk":
        dict_default, affix_default, output_default = "sk_sk.dict", "sk_sk.affix", "sk_sk_fixed.dict"
    else:
        dict_default, affix_default, output_default = "cs_cz.dict", "cs_cz.affix", "cs_cz_fixed.dict"

    dict_file = args.dict or dict_default
    affix_file = args.affix or affix_default
    output_file = args.output or output_default

    dict_path = dict_file if os.path.isabs(dict_file) else os.path.join(script_dir, dict_file)
    affix_path = affix_file if os.path.isabs(affix_file) else os.path.join(script_dir, affix_file)
    output_path = output_file if os.path.isabs(output_file) else os.path.join(script_dir, output_file)
    changelog_path = args.changelog if os.path.isabs(args.changelog) else os.path.join(script_dir, args.changelog)

    # Load language config and set module-level constants
    lang_cfg = LangConfig.from_affix(affix_path, override_lang=args.lang)
    print(f"Language: {lang_cfg.lang}", file=sys.stderr)

    global CONSOLIDATION_FLAGS, FLAG_PRIORITY, FLAG_POS
    CONSOLIDATION_FLAGS = lang_cfg.consolidation_flags
    FLAG_PRIORITY = {f: i for i, f in enumerate(reversed(CONSOLIDATION_FLAGS))}
    FLAG_POS = lang_cfg.flag_pos

    for path, label in [(dict_path, "Dictionary"), (affix_path, "Affix")]:
        if not os.path.exists(path):
            print(f"Error: {label} file not found: {path}", file=sys.stderr)
            sys.exit(1)

    # ---- Step 1: Parse affix rules ----
    print("Step 1: Parsing affix rules...", file=sys.stderr)
    prefixes, suffixes = parse_affix_file(affix_path)
    total_rules = sum(len(v) for v in prefixes.values()) + sum(len(v) for v in suffixes.values())
    print(f"  {len(prefixes)} prefix groups, {len(suffixes)} suffix groups "
          f"({total_rules} rules total)", file=sys.stderr)

    # ---- Step 2: Parse dictionary ----
    print("Step 2: Parsing dictionary...", file=sys.stderr)
    entries = parse_dict_file(dict_path)

    base_lookup = {}
    bare_words_set = set()
    for word, flags, pos in entries:
        base_lookup[word] = (flags, pos)
        if not flags:
            bare_words_set.add(word)

    flagged_count = len(entries) - len(bare_words_set)
    print(f"  {len(entries)} entries  ({len(bare_words_set)} bare, "
          f"{flagged_count} flagged)", file=sys.stderr)

    # ---- Step 3: Reverse morphology ----
    print("Step 3: Reverse morphology on all bare entries...", file=sys.stderr)
    groups = reverse_morphology_all(
        bare_words_set, suffixes, base_lookup, verbose=args.verbose,
    )

    # ---- Step 4: Select consolidations ----
    print("Step 4: Selecting consolidation groups...", file=sys.stderr)
    consolidations, assigned_forms = select_consolidations(
        groups, suffixes, bare_words_set, base_lookup,
        min_group=args.min_group,
        min_coverage=args.min_coverage,
        verbose=args.verbose,
    )

    # ---- Step 5: Verb duplicates ----
    print("Step 5: Finding verb duplicates...", file=sys.stderr)
    verb_dupes = find_verb_duplicates(entries, verb_flags=lang_cfg.verb_flags,
                                      verb_pos=lang_cfg.verb_pos, verbose=args.verbose)
    # Don't remove a verb dupe if it's already handled by consolidation
    verb_dupes -= set(assigned_forms.keys())
    verb_dupes -= {g["base"] for g in consolidations}

    # ---- Report ----
    total_removed = len(assigned_forms) + len(verb_dupes)
    print(f"\n  Consolidation groups:  {len(consolidations)}", file=sys.stderr)
    print(f"  Forms to remove:       {len(assigned_forms)}", file=sys.stderr)
    print(f"  Verb duplicates:       {len(verb_dupes)}", file=sys.stderr)
    print(f"  Total entries removed: {total_removed}", file=sys.stderr)

    if args.verbose and consolidations:
        print(f"\n  Top 20 consolidation groups:", file=sys.stderr)
        for g in consolidations[:20]:
            sample = ", ".join(sorted(g["forms"])[:5])
            print(f"    {g['base']}/{g['flag']} -> {g['score']} forms  "
                  f"({sample}{'...' if g['score'] > 5 else ''})", file=sys.stderr)

    if args.dry_run:
        print("\nDry run — no files written.", file=sys.stderr)
        return

    # ---- Step 6: Rewrite dictionary ----
    print(f"\nStep 6: Writing fixed dictionary to {output_path}...", file=sys.stderr)
    stats, changes = process_dictionary(
        dict_path, output_path,
        consolidations, assigned_forms, verb_dupes,
        verbose=args.verbose,
    )

    # ---- Step 7: Validate ----
    print("Step 7: Validating output (expanding fixed dictionary)...", file=sys.stderr)
    removed_forms = set(assigned_forms.keys())
    missing, total_forms, new_bare, new_entries = validate_output(
        output_path, affix_path, removed_forms, verbose=args.verbose,
    )

    if missing:
        print(f"  WARNING: {len(missing)} forms removed but NOT regenerated!", file=sys.stderr)
        if args.verbose:
            for form in sorted(missing)[:20]:
                print(f"    {form}", file=sys.stderr)
            if len(missing) > 20:
                print(f"    ... and {len(missing) - 20} more", file=sys.stderr)
    else:
        print(f"  All {len(removed_forms)} removed forms verified regenerated.", file=sys.stderr)

    print(f"  Fixed dictionary: {new_entries} entries, {total_forms} expanded forms, "
          f"{new_bare} bare", file=sys.stderr)

    # ---- Step 8: Changelog ----
    print(f"Step 8: Writing changelog to {changelog_path}...", file=sys.stderr)
    write_changelog(
        changelog_path, stats, changes, missing,
        (total_forms, new_bare, new_entries),
    )

    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
