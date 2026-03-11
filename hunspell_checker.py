#!/usr/bin/env python3
"""
Hunspell Dictionary Checker & Extender for PostgreSQL FTS.

Extracts words from a PDF, checks them against the Czech hunspell dictionary
with full affix expansion, and reports missing/broken entries with fix suggestions.
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict


# ---------------------------------------------------------------------------
# 1. PDF Text Extraction
# ---------------------------------------------------------------------------

def extract_text_pdftotext(pdf_path):
    """Extract text using pdftotext (poppler)."""
    try:
        result = subprocess.run(
            ["pdftotext", "-enc", "UTF-8", pdf_path, "-"],
            capture_output=True, timeout=60, encoding="utf-8", errors="replace",
        )
        if result.returncode == 0 and result.stdout and result.stdout.strip():
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def extract_text_pdfminer(pdf_path):
    """Extract text using pdfminer.six."""
    from pdfminer.high_level import extract_text
    return extract_text(pdf_path)


def extract_text(pdf_path):
    """Extract text from PDF, trying pdftotext first, then pdfminer."""
    text = extract_text_pdftotext(pdf_path)
    if text:
        return text
    print("  pdftotext failed, falling back to pdfminer...", file=sys.stderr)
    return extract_text_pdfminer(pdf_path)


def rejoin_hyphens(text):
    """Rejoin soft-hyphenated and line-break-hyphenated words."""
    # Soft hyphen
    text = text.replace("\u00AD", "")
    # Line-break hyphen: word- \n continuation
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return text


def tokenize(text, word_re=None):
    """Extract unique lowercase words from text using a language-specific regex."""
    if word_re is None:
        from lang_config import CZECH_WORD_RE
        word_re = CZECH_WORD_RE
    text = rejoin_hyphens(text)
    words = set()
    for m in word_re.finditer(text.lower()):
        words.add(m.group())
    return words


# ---------------------------------------------------------------------------
# 2. Affix Rule Parser
# ---------------------------------------------------------------------------

def condition_to_regex(cond):
    """Convert hunspell condition syntax to a Python regex pattern string.

    Hunspell conditions:
      - '.'  matches any character
      - '[abc]' character class
      - '[^abc]' negated class
      - literal characters otherwise
    The condition must match the END of the word (for suffixes) or
    START (for prefixes), but we return the raw pattern and let callers anchor.
    """
    if cond == ".":
        return "."  # match anything (at least one char)
    # The condition is already mostly regex-compatible
    return cond


def parse_affix_file(affix_path):
    """Parse a hunspell .affix file into prefix and suffix rule groups.

    Returns:
        prefixes: {flag: [(strip, add, condition_regex, cross_product)]}
        suffixes: {flag: [(strip, add, condition_regex, cross_product)]}
    """
    prefixes = defaultdict(list)
    suffixes = defaultdict(list)
    current_type = None  # 'PFX' or 'SFX'
    current_flag = None
    cross_product = False

    with open(affix_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("SET "):
                continue

            parts = line.split()
            if len(parts) < 4:
                continue

            rule_type = parts[0]

            if rule_type in ("PFX", "SFX"):
                flag = parts[1]

                # Header line: PFX/SFX flag cross_product count
                if parts[2] in ("Y", "N"):
                    current_type = rule_type
                    current_flag = flag
                    cross_product = parts[2] == "Y"
                    continue

                # Rule line: PFX/SFX flag strip add condition [morphological_info...]
                if flag != current_flag:
                    continue

                strip = parts[2]
                add = parts[3]
                condition = parts[4] if len(parts) > 4 else "."

                # '0' means no strip / no add
                if strip == "0":
                    strip = ""
                if add == "0":
                    add = ""

                target = prefixes if rule_type == "PFX" else suffixes
                target[flag].append((strip, add, condition, cross_product))

    return dict(prefixes), dict(suffixes)


# ---------------------------------------------------------------------------
# 3. Dictionary Expansion
# ---------------------------------------------------------------------------

def parse_dict_file(dict_path):
    """Parse a hunspell .dict file.

    Returns:
        entries: [(word, flags_str, pos)]  — flags_str may be empty for bare entries
    """
    entries = []
    with open(dict_path, encoding="utf-8") as f:
        first_line = True
        for line in f:
            line = line.strip()
            if not line:
                continue
            if first_line:
                first_line = False
                # First line is the count
                if line.isdigit():
                    continue

            # Format: word/FLAGS po:POS  or  word po:POS  or  word/FLAGS  or  word
            # Extract POS
            pos = ""
            pos_match = re.search(r"\bpo:(\S+)", line)
            if pos_match:
                pos = pos_match.group(1)
                line = line[: pos_match.start()].strip()

            # Strip other morphological tags (is:...)
            line = re.sub(r"\bis:\S+", "", line).strip()

            # Split word/flags
            if "/" in line:
                word, flags_str = line.split("/", 1)
                flags_str = flags_str.strip()
            else:
                word = line
                flags_str = ""

            word = word.strip().lower()
            if word:
                entries.append((word, flags_str, pos))

    return entries


def apply_suffix_rule(word, strip, add, condition):
    """Try to apply a suffix rule to a word. Returns the new form or None."""
    # Build the condition regex — must match end of word
    if condition == ".":
        # matches any word
        pass
    else:
        # The condition is anchored to end of word
        # But it's a single-char-class condition applied to the character(s) before stripping
        pattern = condition + "$"
        if not re.search(pattern, word):
            return None

    if strip:
        if word.endswith(strip):
            return word[: -len(strip)] + add
        else:
            return None
    else:
        return word + add


def apply_prefix_rule(word, strip, add, condition):
    """Try to apply a prefix rule to a word. Returns the new form or None."""
    if condition != ".":
        pattern = "^" + condition
        if not re.search(pattern, word):
            return None

    if strip:
        if word.startswith(strip):
            return add + word[len(strip):]
        else:
            return None
    else:
        return add + word


def expand_dictionary(entries, prefixes, suffixes, verbose=False):
    """Expand the dictionary using affix rules.

    Returns:
        form_lookup: {form: [(base_word, flag, pos)]}
        bare_words:  set of words with no flags
        base_lookup: {word: (flags_str, pos)}  — original entries
    """
    form_lookup = defaultdict(list)
    bare_words = set()
    base_lookup = {}

    for word, flags_str, pos in entries:
        base_lookup[word] = (flags_str, pos)

        if not flags_str:
            bare_words.add(word)
            # The bare word itself is "in" the dictionary but won't stem
            form_lookup[word].append((word, "", pos))
            continue

        # The base form always maps to itself
        form_lookup[word].append((word, flags_str, pos))

        flags = list(flags_str)

        # Apply suffix rules
        suffix_forms = []
        for flag in flags:
            if flag in suffixes:
                for strip, add, condition, cross in suffixes[flag]:
                    form = apply_suffix_rule(word, strip, add, condition)
                    if form:
                        form_lookup[form].append((word, flag, pos))
                        suffix_forms.append((form, flag, cross))

        # Apply prefix rules
        for flag in flags:
            if flag in prefixes:
                for strip, add, condition, cross in prefixes[flag]:
                    # Apply prefix to base word
                    form = apply_prefix_rule(word, strip, add, condition)
                    if form:
                        form_lookup[form].append((word, flag, pos))

                    # Cross-product: apply prefix to suffix-expanded forms
                    if cross:
                        for sform, sflag, scross in suffix_forms:
                            if scross:
                                form2 = apply_prefix_rule(sform, strip, add, condition)
                                if form2:
                                    form_lookup[form2].append((word, flag + sflag, pos))

    if verbose:
        print(f"  Expanded to {len(form_lookup)} unique forms", file=sys.stderr)
        print(f"  Bare entries: {len(bare_words)}", file=sys.stderr)

    return dict(form_lookup), bare_words, base_lookup


# ---------------------------------------------------------------------------
# 4. Stopwords
# ---------------------------------------------------------------------------

def load_stopwords(stop_path):
    """Load stopwords from a file (one per line)."""
    words = set()
    with open(stop_path, encoding="utf-8") as f:
        for line in f:
            w = line.strip().lower()
            if w:
                words.add(w)
    return words


# ---------------------------------------------------------------------------
# 5. Word Classification
# ---------------------------------------------------------------------------

# Classification labels
OK = "OK"           # properly generated via affix expansion
BARE = "BARE"       # exists in dict but without flags (broken stemming)
UNKNOWN = "UNKNOWN" # not in dictionary at all
STOPWORD = "STOP"   # in stopword list


def classify_words(pdf_words, form_lookup, bare_words, stopwords):
    """Classify each PDF word.

    Returns dict: {word: (classification, details)}
    where details is a list of (base, flag, pos) for OK words, or empty.
    """
    results = {}
    for word in sorted(pdf_words):
        if word in stopwords:
            results[word] = (STOPWORD, [])
            continue

        if word in form_lookup:
            expansions = form_lookup[word]
            # Check if any expansion comes from a flagged entry (not bare)
            flagged = [(b, f, p) for b, f, p in expansions if f]
            if flagged:
                results[word] = (OK, flagged)
            else:
                # Only bare matches
                results[word] = (BARE, expansions)
        else:
            results[word] = (UNKNOWN, [])

    return results


# ---------------------------------------------------------------------------
# 6. Reverse Morphology (suggestions for UNKNOWN and BARE words)
# ---------------------------------------------------------------------------

def reverse_suffix(word, suffixes, base_lookup):
    """For a word, try reversing each suffix rule to find potential base words.

    Returns list of (reconstructed_base, flag, strip, add, base_exists, base_flags, base_pos)
    """
    suggestions = []
    for flag, rules in suffixes.items():
        for strip, add, condition, _cross in rules:
            if not add:
                # Rule adds nothing — word would be same as base
                continue
            if word.endswith(add):
                # Reverse: remove the suffix addition, restore the strip
                candidate = word[: -len(add)] + strip if add else word + strip
                if not candidate:
                    continue
                # Check condition on the candidate
                if condition != ".":
                    pattern = condition + "$"
                    if not re.search(pattern, candidate):
                        continue
                # Does candidate exist in the dictionary?
                if candidate in base_lookup:
                    base_flags, base_pos = base_lookup[candidate]
                    suggestions.append((candidate, flag, strip, add, True, base_flags, base_pos))
                else:
                    suggestions.append((candidate, flag, strip, add, False, "", ""))
    return suggestions


def reverse_prefix(word, prefixes, base_lookup):
    """For a word, try reversing each prefix rule to find potential base words."""
    suggestions = []
    for flag, rules in prefixes.items():
        for strip, add, condition, _cross in rules:
            if not add:
                continue
            if word.startswith(add):
                candidate = strip + word[len(add):]
                if not candidate:
                    continue
                if candidate in base_lookup:
                    base_flags, base_pos = base_lookup[candidate]
                    suggestions.append((candidate, flag, strip, add, True, base_flags, base_pos))
                else:
                    suggestions.append((candidate, flag, strip, add, False, "", ""))
    return suggestions


def generate_suggestions(word, classification, suffixes, prefixes, base_lookup):
    """Generate fix suggestions for a word.

    Returns list of suggestion dicts.
    """
    suggestions = []

    sfx = reverse_suffix(word, suffixes, base_lookup)
    pfx = reverse_prefix(word, prefixes, base_lookup)

    for candidate, flag, strip, add, exists, base_flags, base_pos in sfx + pfx:
        if exists:
            if flag in base_flags:
                # Base already has this flag — word should be generated
                # This means our expansion might have missed it, or it's an edge case
                continue
            if base_flags:
                # Base exists with other flags — suggest adding the flag
                suggestions.append({
                    "type": "ADD_FLAG",
                    "base": candidate,
                    "current_flags": base_flags,
                    "add_flag": flag,
                    "pos": base_pos,
                    "desc": f"Add flag '{flag}' to existing entry '{candidate}/{base_flags}' → '{candidate}/{base_flags}{flag}'",
                })
            else:
                # Base exists bare — suggest adding flag
                suggestions.append({
                    "type": "ADD_FLAG",
                    "base": candidate,
                    "current_flags": "",
                    "add_flag": flag,
                    "pos": base_pos,
                    "desc": f"Add flag '{flag}' to bare entry '{candidate}' → '{candidate}/{flag}'",
                })
        else:
            # Base doesn't exist — suggest adding new entry
            suggestions.append({
                "type": "ADD_NEW",
                "base": candidate,
                "add_flag": flag,
                "pos": "",
                "desc": f"Add new entry '{candidate}/{flag}'",
            })

    # Deduplicate by base+flag
    seen = set()
    unique = []
    for s in suggestions:
        key = (s.get("base", ""), s.get("add_flag", ""))
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


# ---------------------------------------------------------------------------
# 7. Consolidation Analysis
# ---------------------------------------------------------------------------

def find_consolidation_groups(bare_words, suffixes, base_lookup):
    """Find groups of bare entries that could be a single flagged entry.

    For each suffix flag, try to reverse-engineer bare words to a common base.
    If a base (possibly also bare) generates multiple existing bare forms,
    suggest consolidation.
    """
    # Map: (candidate_base, flag) -> list of bare words it explains
    candidate_groups = defaultdict(list)

    for word in bare_words:
        for flag, rules in suffixes.items():
            for strip, add, condition, _cross in rules:
                if not add:
                    continue
                if word.endswith(add):
                    candidate = word[: -len(add)] + strip
                    if not candidate:
                        continue
                    if condition != ".":
                        pattern = condition + "$"
                        if not re.search(pattern, candidate):
                            continue
                    candidate_groups[(candidate, flag)].append(word)

    # Also check if the candidate base itself is bare
    consolidations = []
    for (candidate, flag), explained_forms in candidate_groups.items():
        if len(explained_forms) < 2:
            continue

        # Check if candidate is in dictionary
        in_dict = candidate in base_lookup
        is_bare = candidate in bare_words

        consolidations.append({
            "base": candidate,
            "flag": flag,
            "forms": sorted(set(explained_forms)),
            "base_in_dict": in_dict,
            "base_is_bare": is_bare,
            "count": len(set(explained_forms)),
        })

    # Sort by number of forms explained (most useful first)
    consolidations.sort(key=lambda x: -x["count"])
    return consolidations


# ---------------------------------------------------------------------------
# 8. Output
# ---------------------------------------------------------------------------

FLAG_DESCRIPTIONS = None  # Set dynamically from LangConfig


def format_report(results, consolidations, form_lookup, bare_words, base_lookup, verbose=False, flag_descriptions=None):
    """Format the classification report."""
    lines = []

    # Counts
    counts = defaultdict(int)
    for word, (cls, _) in results.items():
        counts[cls] += 1

    total = len(results)
    lines.append("=" * 70)
    lines.append("HUNSPELL DICTIONARY CHECK REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Total unique words from PDF:  {total}")
    lines.append(f"  OK (properly stemmed):      {counts[OK]}")
    lines.append(f"  BARE (broken stemming):     {counts[BARE]}")
    lines.append(f"  UNKNOWN (not in dict):      {counts[UNKNOWN]}")
    lines.append(f"  STOPWORD (skipped):         {counts[STOPWORD]}")
    lines.append("")
    lines.append(f"Dictionary stats:")
    lines.append(f"  Total entries:              {len(base_lookup)}")
    lines.append(f"  Bare entries:               {len(bare_words)}")
    lines.append(f"  Flagged entries:            {len(base_lookup) - len(bare_words)}")
    lines.append(f"  Expanded forms:             {len(form_lookup)}")
    lines.append("")

    # BARE words detail
    bare_results = [(w, d) for w, (c, d) in results.items() if c == BARE]
    if bare_results:
        lines.append("-" * 70)
        lines.append(f"BARE WORDS ({len(bare_results)}) — in dict but without affix flags")
        lines.append("-" * 70)
        for word, details in bare_results:
            lines.append(f"  {word}")
        lines.append("")

    # UNKNOWN words detail
    unknown_results = [(w, d) for w, (c, d) in results.items() if c == UNKNOWN]
    if unknown_results:
        lines.append("-" * 70)
        lines.append(f"UNKNOWN WORDS ({len(unknown_results)}) — not in dictionary")
        lines.append("-" * 70)
        for word, details in unknown_results:
            lines.append(f"  {word}")
        lines.append("")

    # OK words (only in verbose mode)
    if verbose:
        ok_results = [(w, d) for w, (c, d) in results.items() if c == OK]
        if ok_results:
            lines.append("-" * 70)
            lines.append(f"OK WORDS ({len(ok_results)}) — properly stemmed")
            lines.append("-" * 70)
            for word, details in ok_results:
                bases = ", ".join(f"{b}/{f}" for b, f, p in details[:3])
                lines.append(f"  {word} ← {bases}")
            lines.append("")

    # Consolidation opportunities
    if consolidations:
        lines.append("-" * 70)
        lines.append(f"CONSOLIDATION OPPORTUNITIES ({len(consolidations)})")
        lines.append("  Groups of bare entries replaceable by a single flagged entry")
        lines.append("-" * 70)
        shown = 0
        for group in consolidations:
            if shown >= 50 and not verbose:
                lines.append(f"  ... and {len(consolidations) - shown} more (use -v to see all)")
                break
            base = group["base"]
            flag = group["flag"]
            flag_desc = (flag_descriptions or {}).get(flag, flag)
            forms = group["forms"]
            status = "exists bare" if group["base_is_bare"] else (
                "exists flagged" if group["base_in_dict"] else "NEW base")
            lines.append(f"  {base}/{flag} ({flag_desc}) [{status}]")
            lines.append(f"    Would cover: {', '.join(forms[:10])}")
            if len(forms) > 10:
                lines.append(f"    ... and {len(forms) - 10} more forms")
            shown += 1
        lines.append("")

    return "\n".join(lines)


def format_suggestions_file(results, suffixes, prefixes, base_lookup):
    """Generate a .dict additions file with suggestions."""
    lines = []
    lines.append("# Suggested dictionary additions/modifications")
    lines.append("# Generated by hunspell_checker.py")
    lines.append("#")
    lines.append("# Types:")
    lines.append("#   ADD_FLAG  — add affix flag to existing entry")
    lines.append("#   ADD_NEW   — add new entry to dictionary")
    lines.append("#")
    lines.append("")

    add_flag_suggestions = []
    add_new_suggestions = []

    problem_words = [(w, c, d) for w, (c, d) in results.items() if c in (BARE, UNKNOWN)]

    for word, cls, details in problem_words:
        suggs = generate_suggestions(word, cls, suffixes, prefixes, base_lookup)
        for s in suggs:
            if s["type"] == "ADD_FLAG":
                add_flag_suggestions.append((word, s))
            elif s["type"] == "ADD_NEW":
                add_new_suggestions.append((word, s))

    # Deduplicate and group ADD_FLAG by base
    flag_by_base = defaultdict(list)
    for word, s in add_flag_suggestions:
        flag_by_base[s["base"]].append((word, s))

    if flag_by_base:
        lines.append("# === ADD_FLAG suggestions ===")
        lines.append("# Modify existing entries to add affix flags")
        lines.append("")
        seen_bases = set()
        for base, items in sorted(flag_by_base.items()):
            if base in seen_bases:
                continue
            seen_bases.add(base)
            flags_to_add = set()
            covered_words = set()
            pos = ""
            current_flags = ""
            for word, s in items:
                flags_to_add.add(s["add_flag"])
                covered_words.add(word)
                if s.get("pos"):
                    pos = s["pos"]
                if s.get("current_flags"):
                    current_flags = s["current_flags"]

            new_flags = current_flags + "".join(sorted(flags_to_add - set(current_flags)))
            pos_str = f" po:{pos}" if pos else ""
            lines.append(f"# Covers: {', '.join(sorted(covered_words)[:5])}")
            lines.append(f"{base}/{new_flags}{pos_str}")
            lines.append("")

    # ADD_NEW suggestions
    new_by_base = defaultdict(list)
    for word, s in add_new_suggestions:
        new_by_base[s["base"]].append((word, s))

    if new_by_base:
        lines.append("# === ADD_NEW suggestions ===")
        lines.append("# New entries to add to the dictionary")
        lines.append("")
        seen_bases = set()
        for base, items in sorted(new_by_base.items()):
            if base in seen_bases:
                continue
            seen_bases.add(base)
            flags = set()
            covered = set()
            for word, s in items:
                flags.add(s["add_flag"])
                covered.add(word)
            flags_str = "".join(sorted(flags))
            lines.append(f"# Covers: {', '.join(sorted(covered)[:5])}")
            lines.append(f"{base}/{flags_str}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 9. CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Check PDF words against Czech hunspell dictionary and suggest fixes."
    )
    parser.add_argument("pdf", help="Path to PDF file to analyze")
    parser.add_argument("--dict", help="Path to hunspell .dict file (default: auto from --lang)")
    parser.add_argument("--affix", help="Path to hunspell .affix file (default: auto from --lang)")
    parser.add_argument("--stop", help="Path to stopwords file (default: auto from --lang)")
    parser.add_argument("--lang", help="Language code (cs/sk). Auto-detected from affix file if not set.")
    parser.add_argument("-o", "--output", help="Write report to file (default: stdout)")
    parser.add_argument("-s", "--suggestions", help="Write suggestions file (.dict additions)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    from lang_config import LangConfig

    # Resolve paths relative to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Determine defaults based on language
    lang_hint = args.lang
    if not lang_hint and args.affix:
        # Try to detect from affix file
        affix_test = args.affix if os.path.isabs(args.affix) else os.path.join(script_dir, args.affix)
        if os.path.exists(affix_test):
            from lang_config import detect_language
            lang_hint = detect_language(affix_test)

    # Set defaults based on detected/specified language
    if lang_hint == "sk":
        dict_default, affix_default, stop_default = "sk_sk.dict", "sk_sk.affix", "slovak.stop"
    else:
        dict_default, affix_default, stop_default = "cs_cz.dict", "cs_cz.affix", "czech.stop"

    dict_file = args.dict or dict_default
    affix_file = args.affix or affix_default
    stop_file = args.stop or stop_default

    dict_path = dict_file if os.path.isabs(dict_file) else os.path.join(script_dir, dict_file)
    affix_path = affix_file if os.path.isabs(affix_file) else os.path.join(script_dir, affix_file)
    stop_path = stop_file if os.path.isabs(stop_file) else os.path.join(script_dir, stop_file)
    pdf_path = args.pdf if os.path.isabs(args.pdf) else os.path.join(script_dir, args.pdf)

    for path, label in [(pdf_path, "PDF"), (dict_path, "Dictionary"), (affix_path, "Affix"), (stop_path, "Stopwords")]:
        if not os.path.exists(path):
            print(f"Error: {label} file not found: {path}", file=sys.stderr)
            sys.exit(1)

    # Load language config
    lang_cfg = LangConfig.from_affix(affix_path, override_lang=args.lang)
    print(f"Language: {lang_cfg.lang}", file=sys.stderr)

    # Step 1: Extract PDF text
    print("Extracting text from PDF...", file=sys.stderr)
    text = extract_text(pdf_path)
    pdf_words = tokenize(text, word_re=lang_cfg.word_re)
    print(f"  Found {len(pdf_words)} unique words", file=sys.stderr)

    # Step 2: Parse affix rules
    print("Parsing affix rules...", file=sys.stderr)
    prefixes, suffixes = parse_affix_file(affix_path)
    total_rules = sum(len(v) for v in prefixes.values()) + sum(len(v) for v in suffixes.values())
    print(f"  {len(prefixes)} prefix groups, {len(suffixes)} suffix groups ({total_rules} rules)", file=sys.stderr)

    # Step 3: Parse and expand dictionary
    print("Parsing dictionary...", file=sys.stderr)
    entries = parse_dict_file(dict_path)
    print(f"  {len(entries)} entries", file=sys.stderr)

    print("Expanding dictionary with affix rules...", file=sys.stderr)
    form_lookup, bare_words, base_lookup = expand_dictionary(entries, prefixes, suffixes, verbose=args.verbose)

    # Step 4: Load stopwords
    stopwords = load_stopwords(stop_path)
    print(f"  {len(stopwords)} stopwords loaded", file=sys.stderr)

    # Step 5: Classify words
    print("Classifying words...", file=sys.stderr)
    results = classify_words(pdf_words, form_lookup, bare_words, stopwords)

    # Step 6: Consolidation analysis (only on bare words found in PDF)
    print("Analyzing consolidation opportunities...", file=sys.stderr)
    pdf_bare = {w for w, (c, _) in results.items() if c == BARE}
    consolidations = find_consolidation_groups(pdf_bare, suffixes, base_lookup)

    # Step 7: Generate report
    report = format_report(results, consolidations, form_lookup, bare_words, base_lookup,
                           verbose=args.verbose, flag_descriptions=lang_cfg.flag_descriptions)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)

    # Step 8: Generate suggestions file
    if args.suggestions:
        print("Generating suggestions...", file=sys.stderr)
        suggestions = format_suggestions_file(results, suffixes, prefixes, base_lookup)
        with open(args.suggestions, "w", encoding="utf-8") as f:
            f.write(suggestions)
        print(f"Suggestions written to {args.suggestions}", file=sys.stderr)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
