# Biblical Hebrew Morphological FST

A Finite State Transducer for Biblical Hebrew morphology, built strictly on the
attested data in the **Macula Hebrew** corpus. The system is bidirectional:
given a surface form it returns all valid morphological analyses; given a
lemma + feature bundle it generates the surface form.

The final artifact is a complete lookup table (`output/forms.csv` /
`output/forms.sqlite`) covering every attested root/stem combination with
gap-filled paradigm cells clearly marked as `attested` or `generated`.

### Gap-Filling

For each (lemma, stem) pair that is attested in Macula, missing paradigm cells are
automatically generated to complete the paradigm. This ensures full coverage while
maintaining data-driven integrity:

- If Macula has ANY form for (lemma, stem) → generate missing cells
- If Macula has NO form for that stem → no gap-filling (we only generate for attested stems)

---

## Repository Layout

```
data/           Raw Macula TSV + generated JSON catalogs
lexicon/        LEXC source files (roots, stems, affixes)
phonology/      XFST/HFST rewrite-rule cascades
scripts/        Python utilities (extraction, validation, export)
tests/          Gold test set and unit tests
build/          Compiled .hfst / .foma artifacts
output/         Final CSV and SQLite deliverables
```

---

## Encoding Convention

### Script

All Hebrew text is stored and processed in **Unicode, NFC-normalised, with full
Niqqud** (vowel points). Cantillation marks (te'amim, U+0591–U+05AF) are
stripped at all processing boundaries — the system works with niqqud only.

Use `unicodedata.normalize("NFC", text)` whenever reading Hebrew strings from
external sources.

### Diacritics reference

| Category | Unicode range | Examples |
|---|---|---|
| Cantillation (stripped) | U+0591–U+05AF | ֑ ֒ ֣ ֤ |
| Vocal shewa & hateph | U+05B0–U+05B3 | ְ ֱ ֲ ֳ |
| Hiriq | U+05B4 | ִ |
| Tsere, Segol | U+05B5–U+05B6 | ֵ ֶ |
| Patach, Qamets | U+05B7–U+05B8 | ַ ָ |
| Holam | U+05B9–U+05BA | ֹ ֺ |
| Qibbuts | U+05BB | ֻ |
| Dagesh / Mappiq | U+05BC | ּ |
| Meteg | U+05BD | ֽ |
| Maqaf | U+05BE | ־ |
| Rafe | U+05BF | ֿ |
| Paseq | U+05C0 | ׀ |
| Shin / Sin dot | U+05C1–U+05C2 | ׁ ׂ |
| Sof pasuq | U+05C3 | ׃ |
| Upper/lower dot | U+05C4–U+05C5 | ׄ ׅ |
| Qamets qatan | U+05C7 | ׇ |

### Transliteration (internal / SBL academic)

Transliteration is used only in rule comments and documentation. The system
processes native Hebrew script throughout; transliteration is never stored in
data files.

| Hebrew | Translit | Hebrew | Translit | Hebrew | Translit |
|--------|----------|--------|----------|--------|----------|
| א | ʾ | ל | l | ק | q |
| ב | b | מ/ם | m | ר | r |
| ג | g | נ/ן | n | שׁ | š |
| ד | d | ס | s | שׂ | ś |
| ה | h | ע | ʿ | ת | t |
| ו | w | פ/ף | p / f | | |
| ז | z | צ/ץ | ṣ | | |
| ח | ḥ | | | | |
| ט | ṭ | | | | |
| י | y | | | | |
| כ/ך | k / ḵ | | | | |

Vowel transliteration:

| Vowel | Name | Translit |
|-------|------|----------|
| ַ | Patach | a |
| ָ | Qamets | ā |
| ֶ | Segol | e |
| ֵ | Tsere | ē |
| ִ | Hiriq | i |
| ִי | Hiriq + mater | î |
| ָ (short) | Qamets hatuf | o |
| ֹ | Holam | ō |
| ֻ | Qibbuts | u |
| וּ | Shureq | û |
| ְ | Vocal shewa | ə |
| ֱ | Hateph segol | ĕ |
| ֲ | Hateph patach | ă |
| ֳ | Hateph qamets | ŏ |

---

## Root Classification

Roots are classified by the weak properties of their consonants. A root may
belong to more than one category; in that case `doubly-weak` is also assigned.

| Tag | Condition |
|-----|-----------|
| `strong` | No weak consonants |
| `I-aleph` | C1 = א |
| `I-nun` | C1 = נ |
| `I-waw` | C1 = ו |
| `I-yod` | C1 = י |
| `I-guttural` | C1 ∈ {ה ח ע ר} (not aleph, which has its own tag) |
| `II-guttural` | C2 ∈ {א ה ח ע ר} |
| `hollow` | C2 ∈ {ו י} with a following C3 |
| `III-he` | C3 = ה |
| `III-aleph` | C3 = א |
| `III-guttural` | C3 ∈ {ח ע ר} |
| `geminate` | C2 = C3 |
| `doubly-weak` | Two or more of the above apply |

---

## Toolchain

### HFST (primary)

[Helsinki Finite-State Technology](https://hfst.github.io) — installed as a
Python package via uv:

```
uv add hfst
```

HFST compiles LEXC lexicons and XFST-style rewrite rules and provides Python
bindings for generation and analysis at runtime.

Quick sanity check:

```python
import hfst
t = hfst.regex('b a r ā ʾ : b ā r ā ʾ')
print(t)   # should print the transducer arc table
```

### Foma (secondary / cross-check)

[Foma](https://github.com/mhulden/foma) — installed via Homebrew:

```
brew install foma
```

Foma reads the same LEXC/XFST source files and is useful for interactive
debugging (`foma -l lexicon/roots.lexc` drops into a REPL).

### Running the extraction pipeline

```bash
# Step 1: Extract from Macula TSV
uv run python scripts/extract.py

# Step 2: Generate gap-filled lookup table
uv run python scripts/generate_gaps.py

# Step 3: Export to SQLite
uv run python scripts/export_sqlite.py
```

Produces:
- `data/attestation.json` — all attested forms
- `data/root_classes.json` — root classifications  
- `data/gaps.json` — missing paradigm cells
- `output/forms.csv` — complete lookup table (attested + generated)
- `output/forms.sqlite` — SQLite database

### Running tests

```bash
uv run pytest
```

---

## Data Sources

- **Macula Hebrew** (`data/macula-hebrew.tsv`) — word-level morphological
  annotation of the Hebrew Bible. Each token carries lemma, stem (binyan),
  part of speech, person/gender/number/state, and a surface Unicode form.
  Aramaic portions are present in the file and are filtered out during
  extraction (`lang == "H"` tokens only).

---

## Linguistic References

Rule files cite section numbers from the following grammars:

- **JM** — Joüon, P. & Muraoka, T. *A Grammar of Biblical Hebrew*. Rome: PIB.
- **GKC** — Gesenius, W., Kautzsch, E. & Cowley, A. E. *Gesenius' Hebrew
  Grammar*. Oxford: Clarendon.
- **WOC** — Waltke, B. K. & O'Connor, M. *An Introduction to Biblical Hebrew
  Syntax*. Winona Lake: Eisenbrauns.

---

## Coverage Metrics

| Metric | Value |
|--------|-------|
| Total Forms | 55,237 |
| Attested Forms | 31,092 |
| Generated Forms | 24,145 |
| Unique Surfaces | 43,643 |
| Unique Lemmas | 8,026 |
| Unique Cells | 540 |
| Paradigm Fill Rate | 100% |

### By Stem

| Stem | Attested | Generated | Total |
|------|---------|----------|-------|
| qal | 21,832 | 9,161 | 30,993 |
| hiphil | 3,691 | 4,080 | 7,771 |
| piel | 2,454 | 3,308 | 5,762 |
| niphal | 1,703 | 3,541 | 5,244 |
| hithpael | 477 | 1,523 | 2,000 |
| pual | 303 | 1,608 | 1,911 |
| hophal | 204 | 924 | 1,128 |

### By Type

| Type | Count |
|------|-------|
| common (noun) | 9,325 |
| yiqtol | 4,542 |
| qatal | 3,827 |
| proper | 2,714 |
| wayyiqtol | 2,340 |
| participle active | 2,075 |
| weqatal | 1,780 |
| infinitive construct | 1,306 |
| imperative | 1,090 |
| participle passive | 639 |
| jussive | 551 |
| infinitive absolute | 338 |
| gentilic | 295 |
| cohortative | 270 |

---

## Scope Notes

- **Ketiv/Qere**: out of scope for v1; a `ketiv_qere` column is reserved in
  the output schema for future use.
- **Accents (te'amim)**: explicitly out of scope. Niqqud only.
- **Aramaic**: Daniel and Ezra Aramaic tokens are present in Macula but
  excluded from all catalogs (`lang != "H"`).
- **Ambiguity**: the FST returns *all* valid analyses for a surface form.
  Multiple rows per surface form in the output table are expected and correct.
