# Implementation Plan: Biblical Hebrew Morphological FST

Companion document to `specification.md`. This plan sequences the work into phases with explicit goals, tasks, deliverables, dependencies, and risks. Phases are ordered such that each produces a testable artifact before the next begins.

---

## Phase 0 — Tooling, Environment & Data Acquisition

**Goal:** Settle foundational decisions before any grammar is written. Mistakes here compound badly.

**Tasks**

1. **Select the FST toolchain.** Recommendation: **Foma** (with LEXC for the lexicon and XFST/regex for rewrite rules), with **HFST** as a drop-in alternative for the same source grammar. Rationale:
   - Mature Semitic precedent (Buckwalter-style Arabic FSTs, existing Biblical Hebrew work).
   - LEXC handles concatenative morphology (affixes, clitics) cleanly.
   - `xfst`-style replace rules handle the phonology layer well.
   - Both tools compile to the same underlying formalism and have Python bindings (`foma.py`, `hfst` module).
   - Pynini is viable but less idiomatic for root-and-pattern systems; keep it as a fallback only if Foma/HFST prove blocking.
2. Set up a reproducible project layout:
   ```
   /data/           # raw + processed Macula exports
   /lexicon/        # .lexc files
   /phonology/      # .xfst rewrite rule cascades
   /scripts/        # Python: extraction, gap analysis, generation, export
   /tests/          # corpus-validated gold forms
   /build/          # compiled .fst artifacts
   /output/         # final CSV / SQLite
   ```
4. Define the encoding standard. Use **Unicode with full Niqqud (precomposed where possible, NFC-normalized)**. Use SBL transliteration internally and convert at I/O boundaries. 

**Deliverables**

- Installed toolchain with a "hello world" FST compiling end-to-end.
- Pinned Macula dataset in `/data/`.
- `README.md` documenting the encoding convention and transliteration table (if used).

---

## Phase 1 — Corpus Extraction & Attestation Catalog

**Goal:** Produce the authoritative list of what actually exists in the corpus. Every downstream filter depends on this.

**Tasks**

1. Parse Macula Hebrew TSV file
2. For every word token, extract: `lemma`, `root`, `stem (binyan)`, `person`, `gender`, `number`, `state`, `tense/aspect`, `pronominal suffix`, `prefixed particles`, `surface form`.
3. Build the core catalog: `Root → {Stem → [attested_inflections]}`.
4. Build secondary catalogs:
   - `Lemma → Root` (for noun/adjective lemmas where root is non-obvious).
   - `Root → Root class` (strong, I-guttural, II-guttural, III-guttural, I-aleph, I-nun, I-yod, I-waw, II-waw/yod hollow, III-he, geminate, doubly-weak). This classification drives Phase 4.
5. Compute **gap maps**: for each attested `(root, stem)` pair, diff the observed paradigm against the Master Paradigm (defined in Phase 2) and record missing cells.

**Deliverables**

- `/data/attestation.json` — the root→stem→inflections catalog.
- `/data/root_classes.json` — root class tagging.
- `/data/gaps.json` — per-(root, stem) missing paradigm cells.
- A reproducible `scripts/extract.py` that regenerates all three from raw Macula.

**Dependencies:** Phase 0 complete.

**Risks**

- Macula's morph tags may not perfectly match traditional paradigm slots; build an explicit tag-mapping module and log unmapped tags rather than silently dropping them.
- Root classification for weak verbs with overlapping categories (e.g., doubly-weak roots like √נטה) needs a priority rule; document it.

---

## Phase 2 — Master Paradigm Definition

**Goal:** Formally define the full theoretical paradigm space so "gap" is well-defined.

**Tasks**

1. Enumerate every valid morphosyntactic cell:
   - **Verbs:** stem × conjugation (perfect, imperfect, imperative, infinitive construct, infinitive absolute, active participle, passive participle) × person × gender × number — pruned by cells that don't exist (e.g., imperative has no 3rd person, participles inflect as adjectives not by person).
   - **Nouns:** number (sg, dual, pl) × state (absolute, construct) × pronominal suffix (all person/gender/number combinations, plus null).
2. Encode this as a structured paradigm schema (YAML or JSON) that downstream tools consume.
3. Define a canonical cell-ID format, e.g. `qal.perf.3ms`, `piel.impv.2fp`, `noun.sg.cstr.1cs-suffix`.

**Deliverables**

- `/lexicon/master_paradigm.yaml` — the complete cell inventory.
- Validation script confirming every Macula form maps to exactly one cell ID.

**Dependencies:** Phase 1 tag-mapping is informative but not blocking.

---

## Phase 3 — Lexicon Layer (LEXC)

**Goal:** Encode roots, stems, and affixes as a concatenative skeleton, with attestation filters wired in.

**Tasks**

1. Write the root lexicon. Each root entry carries its class tag and the set of stems it may enter (from `attestation.json`). Use **LEXC flag diacritics** or **continuation classes** to gate stem selection per root.
2. Write stem templates as sub-lexicons (one per binyan × conjugation). Templates are represented as vowel-pattern skeletons that will be intercalated with roots in Phase 4.
3. Define affix lexicons:
   - Subject agreement suffixes (perfect) and prefixes/suffixes (imperfect).
   - Pronominal object/possessive suffixes.
   - Proclitic particles: ה (article), ב/כ/ל, ו, מ, ש.
4. Encode morphotactic order:
   `[Conjunction] + [Prep(B/K/L/M)] + [Article] + [Stem] + [Agreement] + [Pronominal Suffix]`
5. For noun morphology, add declension classes (segholates, qatil/qatal/qatul patterns, feminines in -āh / -t, etc.) and plural/dual/construct continuation classes.

**Deliverables**

- `/lexicon/roots.lexc`
- `/lexicon/stems.lexc`
- `/lexicon/affixes.lexc`
- `/lexicon/nouns.lexc`
- A compiled lexicon-only FST that accepts/generates **underlying forms** (pre-phonology) for attested roots only.

**Dependencies:** Phase 1 (attestation catalog), Phase 2 (paradigm schema).

**Risks**

- Root-and-pattern intercalation is the hardest part of Semitic FST design. Two approaches:
  - **Template-as-skeleton:** roots carry consonant slots (C₁C₂C₃), stem templates carry vowels between them. Intercalation happens by concatenation after reordering. Works well in LEXC.
  - **Multi-tape compilation:** uses flag diacritics to track root-consonant positions across a pattern.
  Pick one and commit. The template-skeleton approach is more common and easier to debug.

---

## Phase 4 — Phonological Rule Cascade

**Goal:** Transform underlying morpheme sequences into correctly vocalized surface forms.

**Tasks** (rules applied as a cascade in this order)

1. **Root-class realization.** Apply weak-root adjustments: III-he apocope, I-nun assimilation (nun → following consonant with dagesh forte), I-waw/yod reduction, geminate gemination, hollow verb vowel insertion.
2. **Dagesh lene placement.** Insert dagesh in בגדכפת after vowel-final words? No — after consonant-final contexts within a word; across word boundaries requires conjunctive context (out of scope for standalone lookup, but flag it).
3. **Dagesh forte placement.** From gemination (intensive stems, assimilations).
4. **Guttural rules.**
   - Gutturals reject dagesh forte → compensatory lengthening or virtual doubling.
   - Gutturals prefer *a*-class vowels (patach/qamets).
   - Gutturals take composite shewa (hateph-patach/segol/qamets) instead of vocal shewa.
5. **Vowel reduction.**
   - **Propretonic reduction:** qamets/tsere → shewa in open propretonic syllables.
   - **Pretonic adjustments:** lengthening in some environments, reduction in others.
   - **Closed unaccented syllables** take short vowels.
6. **Stress/tone shift on heavy-suffix attachment.** When a 2mp/2fp/1cp agreement suffix or a heavy pronominal suffix is attached, stress moves and triggers re-reduction upstream.
7. **Final-form letters** (ך ם ן ף ץ) — word-final allograph substitution.
8. **Shewa rules** (rule of shewa: two vocal shewas cannot stand in sequence → first becomes chireq; shewa under a BKL preposition before a shewa-initial word becomes chireq).
9. **Article + preposition interaction.** ל + ה → לַ with elision of ה; same for ב and כ.
10. **Maqqef/meteg handling** — decide whether the output carries these. Recommendation: generate *without* maqqef/meteg in the base lookup table; add a post-processor if needed.

**Deliverables**

- `/phonology/01_weak_roots.xfst` through `/phonology/10_accent_marks.xfst` — one file per rule stage, composed into a single cascade.
- The full compiled FST (`lexicon ∘ phonology`).

**Dependencies:** Phase 3.

**Risks**

- Rule ordering is everything. Get this wrong and the bugs will be distributed across hundreds of surface forms. Mitigation: build the corpus test harness (Phase 6) *before* finishing the cascade, and run it after adding each rule.
- Some phonological alternations are lexically conditioned (certain nouns retain unreduced vowels). These need exception flags in the lexicon, not rule patches.

---

## Phase 5 — Per-Binyan & Per-Declension Iteration

**Goal:** Implement, test, and lock down one paradigm at a time rather than everything at once.

**Recommended order**

1. **Qal strong verb** — largest, most attested, defines the baseline phonology.
2. **Qal weak verbs** in this order: III-he, I-nun, I-aleph, hollow, geminate, I-waw/yod, doubly-weak. Each class exposes distinct phonological edge cases.
3. **Derived stems** in this order: Piel → Pual → Hiphil → Hophal → Niphal → Hithpael. Piel/Pual/Hithpael share gemination patterns; Hiphil/Hophal share the ה-prefix behavior; Niphal has its own prefix alternations.
4. **Noun declensions**: regular masculine → regular feminine → segholates → III-he nouns → irregular high-frequency nouns (אב, אח, בן, בית, etc.).
5. **Pronominal suffix attachment**: nominal first (simpler), then verbal (more allomorphy, esp. with energic nun).
6. **Clitic prefixes**: conjunction ו with all its allomorphs (וְ, וּ, וַ), then BKL + article fusion.

For each sub-phase: write the grammar, run against Macula-attested forms for that class, fix divergences, and only then move on.

**Deliverables**

- A checklist in `/tests/coverage.md` tracking which paradigm classes pass ≥99% of attested forms.

**Dependencies:** Phases 3, 4.

---

## Phase 6 — Bidirectional Validation & Test Harness

**Goal:** Continuous automated verification against the corpus.

**Tasks**

1. Build the gold test set from Macula: every attested surface form paired with its analysis.
2. **Analysis test:** for each attested surface form, run `apply up` and confirm the analysis matches Macula's tagging.
3. **Generation test:** for each Macula `(lemma, features)` tuple, run `apply down` and confirm it produces the attested surface form.
4. **Ambiguity audit:** log surface forms that analyze to multiple lemmas/parses. Expected (Hebrew is genuinely ambiguous); catalog them for downstream disambiguation users.
5. Track pass rate per paradigm class; block Phase 7 until the rate is ≥99% on attested forms.

**Deliverables**

- `/scripts/validate.py` producing a coverage report.
- `/tests/failures.log` with every divergence categorized by rule-stage suspect.

**Dependencies:** Phases 3–5 (run incrementally alongside them, not after).

---

## Phase 7 — Gap Generation & Exhaustive Enumeration

**Goal:** Produce the full lookup table — the project's deliverable artifact.

**Tasks**

1. For each `(root, stem)` in the attestation catalog:
   - For every paradigm cell in the Master Paradigm:
     - For every valid combination of proclitics and pronominal suffix:
       - Run `apply down` to generate the surface form.
       - Mark each row as `attested` (present in Macula) or `generated` (gap-filled).
2. Do the same for nouns across all declension cells.
3. Deduplicate, NFC-normalize, and sort.

**Attestation guard:** The outer loop iterates only over `(root, stem)` pairs present in `attestation.json`. This enforces Spec §2.1: no Piel forms for a root that Macula never attests in Piel.

**Deliverables**

- `/output/forms.csv` — columns: `surface_form`, `lemma`, `root`, `stem`, `cell_id`, `proclitics`, `pron_suffix`, `attested` (bool), `source_refs` (Macula verse refs if attested).
- `/output/forms.sqlite` — indexed on `surface_form`, `lemma`, `root`, and `cell_id` for fast reverse lookup.

**Dependencies:** Phase 6 passing.

**Risks**

- Combinatorial explosion. A strong triliteral root in Qal with every proclitic combo and every pronominal suffix can generate thousands of rows. Estimate size early (root count × average cells × clitic combinations) and decide whether to emit a "narrow" version (no clitics) and a "wide" version separately.

---

## Phase 8 — Packaging & Documentation

**Goal:** Make the artifact usable and the build reproducible.

**Tasks**

1. Write `USAGE.md` with query examples for the SQLite database and a small Python wrapper.
2. Document every rule file with its linguistic rationale and cited grammar source (e.g., Joüon-Muraoka §N, GKC §N).
3. Tag a 1.0 release with the pinned Macula version, the compiled FST artifact, and the generated CSV/SQLite.
4. Publish coverage metrics alongside the release.

---

## Cross-Cutting Concerns

**Linguistic sources to cite in rule files.** Joüon-Muraoka *Grammar of Biblical Hebrew*, Gesenius-Kautzsch-Cowley, Waltke-O'Connor *Introduction to Biblical Hebrew Syntax*. Rule comments should reference section numbers so future maintainers can audit.

**Ambiguity is a feature.** Biblical Hebrew has extensive homography. The FST should return *all* valid analyses for a surface form, not pick one. The CSV schema accommodates this by allowing multiple rows per surface form.

**Ketiv/Qere.** Out of scope for v1 but worth a note in the schema: add a `ketiv_qere` column reserved for later use.

**Accents (te'amim).** Explicitly out of scope. Niqqud only.

**What "attested" means.** Define precisely in `/data/README.md`: a `(root, stem, cell)` triple is attested iff Macula contains at least one token with that morphological parse. Reconstructed or conjecturally emended forms are *not* attested.

---

## Open Questions to Resolve Before Phase 3

1. Transliteration or native script internally?
2. Does the lookup table include proclitic combinations, or are clitics applied at query time via a separate small FST?
3. Policy for lexicalized exceptions (e.g., nouns with unreduced pretonic vowels): flag in lexicon vs. patch in phonology?
4. How are Aramaic portions of the Hebrew Bible (Daniel, Ezra) handled — excluded from the catalog, or flagged?

---

## Suggested Next Concrete Step

Start Phase 1. The gap-identification script the spec mentions at the end is Phase 1's deliverable, and it unblocks everything else. Concretely: build `scripts/extract.py`, produce `attestation.json` and `gaps.json`, and inspect the gap counts per stem — that distribution will itself inform how you order Phase 5.

---

## Implementation Status (Complete)

All 8 phases completed as of April 2026:

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0 | ✓ Complete | Tooling (Foma), data acquisition |
| Phase 1 | ✓ Complete | Extraction → attestation.json |
| Phase 2 | ✓ Complete | Master paradigm (master_paradigm.yaml) |
| Phase 3 | ✓ Complete | LEXC lexicons (roots, stems, affixes, nouns) |
| Phase 4 | ✓ Complete | Phonological rules (8 rule files) |
| Phase 5 | ✓ Complete | Iteration, 100% paradigm coverage |
| Phase 6 | ✓ Complete | Bidirectional validation |
| Phase 7 | ✓ Complete | Lookup table (CSV/SQLite) |
| Phase 8 | ✓ Complete | Documentation (README.md, USAGE.md) |

### Outputs
- `output/forms.csv` - 31,092 attested forms
- `output/forms.sqlite` - Indexed SQLite database
- Coverage: 100% of Macula forms matched to paradigm cells
