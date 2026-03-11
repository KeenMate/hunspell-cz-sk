"""
Language-specific configuration for hunspell checker/fixer.

Auto-detects language from the affix file (LANG directive) and provides
the correct word regex, flag descriptions, consolidation flags, etc.
"""

import re

# ---------------------------------------------------------------------------
# Word tokenizer regexes (characters valid in words for each language)
# ---------------------------------------------------------------------------

CZECH_WORD_RE = re.compile(r"[a-záčďéěíňóřšťúůýž]{2,}", re.IGNORECASE)
SLOVAK_WORD_RE = re.compile(r"[a-záäčďéíĺľňóôŕšťúýž]{2,}", re.IGNORECASE)
# Generic fallback: basic Latin + common accented chars
GENERIC_WORD_RE = re.compile(r"[a-záàâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿšžčřďťňěůĺľŕ]{2,}", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Flag descriptions per language
# ---------------------------------------------------------------------------

CZECH_FLAG_DESCRIPTIONS = {
    "N": "negation prefix (ne-)",
    "S": "superlative prefix (nej-)",
    "P": "adjective declension",
    "X": "indeclinable noun",
    "M": "neuter noun (město/moře/stavení)",
    "K": "neuter noun (kuře) / -um nouns",
    "Z": "feminine noun (žena/růže)",
    "L": "feminine noun (kost)",
    "A": "masculine noun (předseda/soudce)",
    "B": "masculine noun (pán)",
    "C": "masculine noun (hrad)",
    "O": "masculine noun (-ek variant)",
    "D": "masculine noun (les)",
    "E": "masculine noun (muž)",
    "F": "masculine noun (stroj)",
    "G": "masculine noun (-ismus)",
    "H": "verb conjugation",
    "I": "verb conjugation (-ovat)",
    "R": "ů→o alternation (dům→dom-)",
    "J": "fleeting-e masculine (příjem→příjm-)",
    "Q": "fleeting-e feminine (povodeň→povodn-)",
    "T": "animate -ník (k→c in nom.pl.)",
    "U": "inanimate -k (k→c in lok.pl.)",
}

SLOVAK_FLAG_DESCRIPTIONS = {
    "N": "negation prefix (ne-)",
    "F": "superlative prefix (naj-)",
    "z": "feminine noun singular (žena)",
    "Z": "feminine noun plural (žena)",
    "U": "feminine noun (ulica variant)",
    "D": "consonant-ending noun paradigm",
    "K": "noun paradigm variant",
    "M": "noun paradigm (-o ending)",
    "S": "noun paradigm (-e ending)",
    "V": "noun paradigm variant",
    "A": "adjective/noun paradigm",
    "c": "animate noun (plural -ia)",
    "C": "animate noun (plural -i)",
    "H": "noun paradigm variant",
    "B": "inanimate noun paradigm (dub)",
    "J": "consonant-ending noun (gen.sg.)",
    "L": "consonant-ending noun variant",
    "O": "neuter noun paradigm",
    "Q": "feminine adjective paradigm",
    "q": "adjective paradigm (gender/number)",
    "Y": "adjective/comparative paradigm",
    "I": "adjective paradigm variant",
    "P": "adjective paradigm variant",
    "X": "verb paradigm (-iať/-liať)",
    "E": "verb paradigm (-ať)",
    "W": "verb paradigm (complex -ať/-iať/-ť/-uť)",
    "T": "verb paradigm",
    "R": "verb paradigm",
    "b": "noun variant (dub with -u G, -e L)",
    "n": "numeral paradigm",
}

# ---------------------------------------------------------------------------
# Consolidation flags per language (which flags to try for bare-word grouping)
# ---------------------------------------------------------------------------

# Czech: noun + adjective paradigms (verbs handled separately via verb-dupe removal)
CZECH_CONSOLIDATION_FLAGS = [
    "P", "Z", "M", "C", "L", "F", "K", "G", "O", "B", "D", "E", "A",
    "R", "J", "Q", "T", "U",
]

# Slovak: noun + adjective paradigms
SLOVAK_CONSOLIDATION_FLAGS = [
    "Y", "I", "P",                                # adjective paradigms
    "z", "Z", "U", "D", "K", "M", "S", "A",       # noun paradigms (non-animate)
    "c", "C", "H", "B", "J", "L", "O", "Q", "V",  # noun paradigms (animate + others)
    "b", "n", "q",                                  # minor paradigms
]

# POS tag to assign when creating new flagged entries
CZECH_FLAG_POS = {
    "P": "adjective",
    "Z": "noun", "M": "noun", "C": "noun", "L": "noun", "F": "noun",
    "K": "noun", "G": "noun", "O": "noun", "B": "noun", "D": "noun",
    "E": "noun", "A": "noun", "R": "noun", "J": "noun", "Q": "noun",
    "T": "noun", "U": "noun",
}

SLOVAK_FLAG_POS = {
    "Y": "adjective", "I": "adjective", "P": "adjective", "Q": "adjective", "q": "adjective",
    "z": "noun", "Z": "noun", "U": "noun", "D": "noun", "K": "noun",
    "M": "noun", "S": "noun", "V": "noun", "A": "noun", "c": "noun",
    "C": "noun", "H": "noun", "B": "noun", "J": "noun", "L": "noun",
    "O": "noun", "b": "noun", "n": "noun",
}

# Verb flags per language (for verb duplicate detection)
CZECH_VERB_FLAGS = {"N"}  # Czech verbs have /N po:verb
CZECH_VERB_POS = "verb"

SLOVAK_VERB_FLAGS = {"W", "E", "X", "T", "R"}  # Slovak verb flags
SLOVAK_VERB_POS = "verb"

# ---------------------------------------------------------------------------
# Language detection & config bundling
# ---------------------------------------------------------------------------

def detect_language(affix_path):
    """Detect language from the LANG directive in the affix file.

    Returns 'cs', 'sk', or None.
    """
    try:
        with open(affix_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LANG "):
                    lang = line.split()[1].strip().lower()
                    if lang in ("cs", "sk"):
                        return lang
                # Stop after first 20 lines
                if line.startswith("SFX") or line.startswith("PFX"):
                    break
    except OSError:
        pass
    return None


class LangConfig:
    """Bundled language configuration."""

    def __init__(self, lang):
        self.lang = lang

        if lang == "cs":
            self.word_re = CZECH_WORD_RE
            self.flag_descriptions = CZECH_FLAG_DESCRIPTIONS
            self.consolidation_flags = CZECH_CONSOLIDATION_FLAGS
            self.flag_pos = CZECH_FLAG_POS
            self.verb_flags = CZECH_VERB_FLAGS
            self.verb_pos = CZECH_VERB_POS
        elif lang == "sk":
            self.word_re = SLOVAK_WORD_RE
            self.flag_descriptions = SLOVAK_FLAG_DESCRIPTIONS
            self.consolidation_flags = SLOVAK_CONSOLIDATION_FLAGS
            self.flag_pos = SLOVAK_FLAG_POS
            self.verb_flags = SLOVAK_VERB_FLAGS
            self.verb_pos = SLOVAK_VERB_POS
        else:
            # Fallback: use generic regex, empty descriptions
            self.word_re = GENERIC_WORD_RE
            self.flag_descriptions = {}
            self.consolidation_flags = []
            self.flag_pos = {}
            self.verb_flags = set()
            self.verb_pos = "verb"

    @classmethod
    def from_affix(cls, affix_path, override_lang=None):
        """Create LangConfig by auto-detecting language from affix file."""
        lang = override_lang or detect_language(affix_path) or "cs"
        return cls(lang)
