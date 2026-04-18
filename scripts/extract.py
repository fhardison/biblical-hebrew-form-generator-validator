#!/usr/bin/env python3
"""
Phase 1: Corpus Extraction & Attestation Catalog
Parses Macula Hebrew TSV and produces:
  - data/attestation.json  — lemma → stem → [attested inflections]
  - data/root_classes.json — lemma → root class tags
  - data/gaps.json         — (lemma, stem) → missing paradigm cells
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
MACULA_TSV = DATA_DIR / "macula-hebrew.tsv"

# ─── Hebrew character sets ────────────────────────────────────────────────────

GUTTURALS = set("אהחער")
ALEPH = "א"
HE    = "ה"
WAW   = "ו"
YOD   = "י"
NUN   = "נ"

# Standard seven binyanim (Aramaic and rare stems excluded from gap analysis)
STANDARD_STEMS = {
    "qal", "niphal", "piel", "pual", "hiphil", "hophal", "hithpael"
}

# ─── Paradigm definition (preliminary; will be formalised in Phase 2) ────────
# Each cell is a frozenset of feature key=value pairs that uniquely names it.
# Cells are represented as tuples of (type, person, gender, number, state).
# State is used for participles and infinitives; person is empty for those.

def _cell(type_, person="", gender="", number="", state=""):
    return (type_, person, gender, number, state)


VERB_PARADIGM: list[tuple] = (
    # ── Qatal (perfect) ──────────────────────────────────────────────────────
    [_cell("qatal", p, g, n) for p, g, n in [
        ("third",  "masculine", "singular"),
        ("third",  "feminine",  "singular"),
        ("second", "masculine", "singular"),
        ("second", "feminine",  "singular"),
        ("first",  "common",    "singular"),
        ("third",  "common",    "plural"),
        ("second", "masculine", "plural"),
        ("second", "feminine",  "plural"),
        ("first",  "common",    "plural"),
    ]] +
    # ── Yiqtol (imperfect) ───────────────────────────────────────────────────
    [_cell("yiqtol", p, g, n) for p, g, n in [
        ("third",  "masculine", "singular"),
        ("third",  "feminine",  "singular"),
        ("second", "masculine", "singular"),
        ("second", "feminine",  "singular"),
        ("first",  "common",    "singular"),
        ("third",  "masculine", "plural"),
        ("third",  "feminine",  "plural"),
        ("second", "masculine", "plural"),
        ("second", "feminine",  "plural"),
        ("first",  "common",    "plural"),
    ]] +
    # ── Wayyiqtol ────────────────────────────────────────────────────────────
    [_cell("wayyiqtol", p, g, n) for p, g, n in [
        ("third",  "masculine", "singular"),
        ("third",  "feminine",  "singular"),
        ("second", "masculine", "singular"),
        ("second", "feminine",  "singular"),
        ("first",  "common",    "singular"),
        ("third",  "masculine", "plural"),
        ("third",  "feminine",  "plural"),
        ("second", "masculine", "plural"),
        ("second", "feminine",  "plural"),
        ("first",  "common",    "plural"),
    ]] +
    # ── Weqatal ──────────────────────────────────────────────────────────────
    [_cell("weqatal", p, g, n) for p, g, n in [
        ("third",  "masculine", "singular"),
        ("third",  "feminine",  "singular"),
        ("second", "masculine", "singular"),
        ("second", "feminine",  "singular"),
        ("first",  "common",    "singular"),
        ("third",  "common",    "plural"),
        ("second", "masculine", "plural"),
        ("second", "feminine",  "plural"),
        ("first",  "common",    "plural"),
    ]] +
    # ── Jussive ──────────────────────────────────────────────────────────────
    [_cell("jussive", p, g, n) for p, g, n in [
        ("third",  "masculine", "singular"),
        ("third",  "feminine",  "singular"),
        ("second", "masculine", "singular"),
        ("second", "feminine",  "singular"),
        ("third",  "masculine", "plural"),
        ("third",  "feminine",  "plural"),
        ("second", "masculine", "plural"),
        ("second", "feminine",  "plural"),
    ]] +
    # ── Cohortative ──────────────────────────────────────────────────────────
    [_cell("cohortative", p, g, n) for p, g, n in [
        ("first",  "common", "singular"),
        ("first",  "common", "plural"),
    ]] +
    # ── Imperative ───────────────────────────────────────────────────────────
    [_cell("imperative", p, g, n) for p, g, n in [
        ("second", "masculine", "singular"),
        ("second", "feminine",  "singular"),
        ("second", "masculine", "plural"),
        ("second", "feminine",  "plural"),
    ]] +
    # ── Participle active ─────────────────────────────────────────────────────
    [_cell("participle active", "", g, n, s) for g, n, s in [
        ("masculine", "singular", "absolute"),
        ("masculine", "singular", "construct"),
        ("feminine",  "singular", "absolute"),
        ("feminine",  "singular", "construct"),
        ("masculine", "plural",   "absolute"),
        ("masculine", "plural",   "construct"),
        ("feminine",  "plural",   "absolute"),
        ("feminine",  "plural",   "construct"),
    ]] +
    # ── Participle passive ────────────────────────────────────────────────────
    [_cell("participle passive", "", g, n, s) for g, n, s in [
        ("masculine", "singular", "absolute"),
        ("masculine", "singular", "construct"),
        ("feminine",  "singular", "absolute"),
        ("masculine", "plural",   "absolute"),
        ("masculine", "plural",   "construct"),
    ]] +
    # ── Infinitive construct ──────────────────────────────────────────────────
    [_cell("infinitive construct")] +
    # ── Infinitive absolute ───────────────────────────────────────────────────
    [_cell("infinitive absolute")]
)

VERB_PARADIGM_SET = set(VERB_PARADIGM)

# Canonical cell-ID string for a cell tuple
def cell_id(cell):
    type_, person, gender, number, state = cell
    parts = [type_]
    if person:
        parts.append(person)
    if gender:
        parts.append(gender)
    if number:
        parts.append(number)
    if state:
        parts.append(state)
    return ".".join(parts)


# ─── Diacritic stripping ──────────────────────────────────────────────────────

def strip_diacritics(text: str) -> str:
    """Strip Hebrew vowel points and cantillation marks (U+0591–U+05C7)."""
    return "".join(c for c in text if not (0x0591 <= ord(c) <= 0x05C7))


# ─── Root classification ──────────────────────────────────────────────────────

def classify_root(lemma: str) -> list[str]:
    """
    Classify a root by its weak-consonant properties.
    Returns a list of category tags (≥1 entry; 'doubly-weak' appended when >1
    primary tag is present).
    """
    consonants = strip_diacritics(lemma)
    if not consonants:
        return ["unknown"]

    c1 = consonants[0] if len(consonants) > 0 else None
    c2 = consonants[1] if len(consonants) > 1 else None
    c3 = consonants[2] if len(consonants) > 2 else None

    cats: list[str] = []

    # ── C1 analysis ──────────────────────────────────────────────────────────
    if c1 == ALEPH:
        cats.append("I-aleph")
    elif c1 == NUN:
        cats.append("I-nun")
    elif c1 == WAW:
        cats.append("I-waw")
    elif c1 == YOD:
        cats.append("I-yod")
    elif c1 in GUTTURALS:
        cats.append("I-guttural")

    # ── C2 analysis ──────────────────────────────────────────────────────────
    if c2 in (WAW, YOD) and c3 is not None and c3 not in (WAW, YOD):
        # Middle waw/yod with a following real consonant → hollow
        cats.append("hollow")
    elif c2 in GUTTURALS:
        cats.append("II-guttural")

    # ── C3 analysis ──────────────────────────────────────────────────────────
    if c3 == HE:
        cats.append("III-he")
    elif c3 == ALEPH:
        cats.append("III-aleph")
    elif c3 in GUTTURALS:
        cats.append("III-guttural")

    # ── Geminate ─────────────────────────────────────────────────────────────
    if c2 is not None and c3 is not None and c2 == c3:
        cats.append("geminate")

    # ── Default to strong ────────────────────────────────────────────────────
    if not cats:
        cats.append("strong")
    elif len(cats) > 1:
        cats.append("doubly-weak")

    return cats


# ─── Morphological feature extraction ────────────────────────────────────────

def row_to_features(row: dict) -> dict:
    """Extract the morphosyntactic feature set from a TSV row."""
    return {
        "type":   row["type"],
        "person": row["person"],
        "gender": row["gender"],
        "number": row["number"],
        "state":  row["state"],
        "morph":  row["morph"],
    }


def features_to_cell(features: dict) -> tuple:
    """Map extracted features to the canonical paradigm cell tuple."""
    # Normalise Macula type strings to paradigm type strings
    type_map = {
        "qatal":               "qatal",
        "yiqtol":              "yiqtol",
        "wayyiqtol":           "wayyiqtol",
        "weqatal":             "weqatal",
        "jussive":             "jussive",
        "cohortative":         "cohortative",
        "imperative":          "imperative",
        "participle active":   "participle active",
        "participle passive":  "participle passive",
        "infinitive construct":"infinitive construct",
        "infinitive absolute": "infinitive absolute",
    }
    type_ = type_map.get(features["type"], features["type"])
    return _cell(
        type_,
        features["person"],
        features["gender"],
        features["number"],
        features["state"],
    )


# ─── Word-group parsing ───────────────────────────────────────────────────────

def parse_word_groups(path: Path):
    """
    Yield word-group dicts, one per surface word position.
    Each dict has:
        ref         – verse reference (e.g. 'GEN 1:1!2')
        head        – the primary morpheme row (verb or noun)
        prefixes    – list of prefix rows (conj, prep, article)
        suffix      – pronominal suffix row or None
        surface     – concatenated text of all morphemes
    """
    current_ref = None
    group: list[dict] = []

    def flush(ref, rows):
        if not rows:
            return None
        surface = "".join(r["text"] for r in rows)
        head = None
        prefixes = []
        suffix = None
        for r in rows:
            pos = r["pos"]
            if pos in ("verb", "noun", "adjective", "pronoun"):
                head = r
            elif pos == "suffix":
                suffix = r
            elif pos in ("conjunction", "preposition", "particle"):
                prefixes.append(r)
        if head is None:
            return None
        return {
            "ref":      ref,
            "head":     head,
            "prefixes": prefixes,
            "suffix":   suffix,
            "surface":  surface,
        }

    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            ref = row["ref"]
            if ref != current_ref:
                wg = flush(current_ref, group)
                if wg:
                    yield wg
                current_ref = ref
                group = []
            group.append(row)
    # flush last group
    wg = flush(current_ref, group)
    if wg:
        yield wg


# ─── Main extraction logic ────────────────────────────────────────────────────

def build_catalogs():
    # attestation[lemma][stem] = list of inflection records
    # Each inflection record = {type, person, gender, number, state, morph,
    #                            pron_suffix, prefixes, surface, refs}
    attestation: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))

    # Keyed sets for deduplication: (lemma, stem) → set of seen feature tuples
    seen: dict[tuple, set] = defaultdict(set)

    # root_classes[lemma] = list of class tags
    root_classes: dict[str, list[str]] = {}

    unmapped_types: set[str] = set()

    print("Parsing Macula Hebrew TSV…")
    total_words = 0
    verb_words  = 0
    noun_words  = 0

    for wg in parse_word_groups(MACULA_TSV):
        total_words += 1
        head = wg["head"]

        # Only process Hebrew tokens (skip Aramaic)
        if head.get("lang") != "H":
            continue

        lemma = head["lemma"]
        pos   = head["pos"]
        stem  = head["stem"]

        # ── Root classification for verbs ─────────────────────────────────
        if pos == "verb" and lemma and lemma not in root_classes:
            root_classes[lemma] = classify_root(lemma)

        # ── Build attestation record ──────────────────────────────────────
        if pos == "verb":
            verb_words += 1
        elif pos == "noun":
            noun_words += 1
        else:
            continue  # skip adjectives, pronouns, etc. for now

        features = row_to_features(head)
        pron_suffix = None
        if wg["suffix"]:
            pron_suffix = {
                "morph":  wg["suffix"]["morph"],
                "person": wg["suffix"]["person"],
                "gender": wg["suffix"]["gender"],
                "number": wg["suffix"]["number"],
            }
        prefix_morphs = [r["morph"] for r in wg["prefixes"]]

        # Dedup key: (type, person, gender, number, state, pron_suffix morph)
        suffix_key = pron_suffix["morph"] if pron_suffix else ""
        dedup_key = (
            features["type"], features["person"], features["gender"],
            features["number"], features["state"], suffix_key
        )
        catalog_key = (lemma, stem)
        if dedup_key in seen[catalog_key]:
            # Still record the ref, but don't create a duplicate entry
            # (find the matching entry and append the ref)
            for entry in attestation[lemma][stem]:
                if (
                    entry["type"]   == features["type"]   and
                    entry["person"] == features["person"]  and
                    entry["gender"] == features["gender"]  and
                    entry["number"] == features["number"]  and
                    entry["state"]  == features["state"]   and
                    entry.get("pron_suffix_morph", "") == suffix_key
                ):
                    if wg["ref"] not in entry["refs"]:
                        entry["refs"].append(wg["ref"])
                    break
            continue

        seen[catalog_key].add(dedup_key)

        entry = {
            "type":              features["type"],
            "person":            features["person"],
            "gender":            features["gender"],
            "number":            features["number"],
            "state":             features["state"],
            "morph":             features["morph"],
            "pron_suffix":       pron_suffix,
            "pron_suffix_morph": suffix_key,
            "prefixes":          prefix_morphs,
            "surface":           wg["surface"],
            "refs":              [wg["ref"]],
        }
        attestation[lemma][stem].append(entry)

        if features["type"] and features["type"] not in {c[0] for c in VERB_PARADIGM_SET} and pos == "verb":
            unmapped_types.add(features["type"])

    print(f"  Total word groups processed : {total_words:>8,}")
    print(f"  Verb word groups            : {verb_words:>8,}")
    print(f"  Noun word groups            : {noun_words:>8,}")

    if unmapped_types:
        print(f"  Unmapped verb type strings  : {sorted(unmapped_types)}")

    # Convert defaultdicts to plain dicts for JSON serialisation
    attestation_out = {
        lemma: {stem: entries for stem, entries in stems.items()}
        for lemma, stems in attestation.items()
    }
    return attestation_out, root_classes


def compute_gaps(attestation: dict) -> dict:
    """
    For each (lemma, stem) that is a standard stem, compute which paradigm
    cells from VERB_PARADIGM are not attested (ignoring pronominal suffixes
    and prefixes at this stage).
    """
    gaps: dict[str, dict[str, list[str]]] = {}

    for lemma, stems in attestation.items():
        for stem, entries in stems.items():
            if stem not in STANDARD_STEMS:
                continue

            # Build set of observed cells
            observed: set[tuple] = set()
            for entry in entries:
                cell = features_to_cell(entry)
                if cell in VERB_PARADIGM_SET:
                    observed.add(cell)

            # Diff against paradigm
            missing = [
                cell_id(c) for c in VERB_PARADIGM if c not in observed
            ]

            if missing:
                if lemma not in gaps:
                    gaps[lemma] = {}
                gaps[lemma][stem] = missing

    return gaps


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    attestation, root_classes = build_catalogs()

    print("\nComputing gap maps…")
    gaps = compute_gaps(attestation)

    # ── Write outputs ─────────────────────────────────────────────────────────
    attestation_path  = DATA_DIR / "attestation.json"
    root_classes_path = DATA_DIR / "root_classes.json"
    gaps_path         = DATA_DIR / "gaps.json"

    print(f"\nWriting {attestation_path}…")
    with attestation_path.open("w", encoding="utf-8") as fh:
        json.dump(attestation, fh, ensure_ascii=False, indent=2)

    print(f"Writing {root_classes_path}…")
    with root_classes_path.open("w", encoding="utf-8") as fh:
        json.dump(root_classes, fh, ensure_ascii=False, indent=2)

    print(f"Writing {gaps_path}…")
    with gaps_path.open("w", encoding="utf-8") as fh:
        json.dump(gaps, fh, ensure_ascii=False, indent=2)

    # ── Summary statistics ────────────────────────────────────────────────────
    total_lemmas   = len(attestation)
    verb_lemmas    = sum(
        1 for stems in attestation.values()
        if any(s in STANDARD_STEMS for s in stems)
    )
    total_pairs    = sum(
        len(stems) for stems in attestation.values()
    )
    gapped_pairs   = sum(len(stems) for stems in gaps.values())
    total_gaps     = sum(
        len(missing)
        for stems in gaps.values()
        for missing in stems.values()
    )

    print("\n── Summary ──────────────────────────────────────────────────────────")
    print(f"  Unique lemmas               : {total_lemmas:>8,}")
    print(f"  Lemmas with standard stems  : {verb_lemmas:>8,}")
    print(f"  (lemma, stem) pairs total   : {total_pairs:>8,}")
    print(f"  Pairs with gaps             : {gapped_pairs:>8,}")
    print(f"  Total missing paradigm cells: {total_gaps:>8,}")
    print("─────────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
