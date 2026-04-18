This is an ambitious and linguistically complex project. To handle the intricate phonological shifts (vowel changes) and the strict data-driven constraints you've specified, an FST (Finite State Transducer) is exactly the right tool. 

Since the end goal is a **lookup table**, we can prioritize morphological accuracy and "over-generation" of theoretical forms over runtime speed.

Here is your technical specification organized into a `specification.md` (or `agents.md`) format.

---

# Technical Specification: Biblical Hebrew Morphological FST

## 1. Project Overview
The goal is to build a Finite State Transducer (FST) that models Biblical Hebrew morphology based strictly on the attested usage in the **Macula Hebrew** dataset. The system will be bidirectional: it must **validate** existing forms and **generate** missing forms in a paradigm, but only for stems (Binyanim) that actually appear in the biblical corpus.

## 2. Core Requirements

### 2.1 Data-Driven Constraints
* **Attestation Filtering:** The FST must not generate forms for a verb stem ($Binyan$) if that specific verb/stem combination is not present in the Macula dataset. 
    * *Example:* If root $\sqrt{qtl}$ appears in *Qal* but never in *Piel*, the FST should reject/not generate *Piel* forms for $\sqrt{qtl}$.
* **Gap Identification:** For every attested stem, the system must identify the "missing" members of the paradigm (Person, Gender, Number, Aspect) and generate them to create a complete theoretical set.

### 2.2 Morphological Scope
* **Verbs:** * Support all 7 major stems ($Qal$, $Niphal$, $Piel$, $Pual$, $Hiphil$, $Hophal$, $Hithpael$).
    * Handle all inflectional categories (Perfect, Imperfect, Imperative, Infinitive, Participle).
* **Nouns:**
    * Generate all forms (Singular, Dual, Plural) in Absolute and Construct states.
* **Affixation (Prefixes & Suffixes):**
    * **Pronominal Suffixes:** Must be attachable to both verbs (object markers) and nouns (possessives).
    * **Prepositional Prefixes:** Handle $ב$, $כ$, $ל$ (BKL) prefixes.
    * **Definite Article:** Handle the $ה$ (He-Heptad) and its interaction with prepositions (elision).

### 2.3 Phonological Engine (Vowel Shifts)
The FST must implement rules for "vowel reduction" and "compensatory lengthening" triggered by:
* **Suffixation:** Account for pre-tonic reduction when heavy suffixes move the stress.
* **Gutturals:** Handle specific shifts (e.g., $a$-coloring) caused by $א, ה, ח, ע, ר$.
* **Syllable Structure:** Ensure vowels change correctly based on open vs. closed syllables.

---

## 3. Implementation Phases

### Phase 1: Data Extraction & Analysis
* **Source:** Parse Macula Hebrew (JSON/CSV formats).
* **Cataloging:** Create a map of `Root -> Attested Stems`.
* **Gap Mapping:** Compare attested forms against a "Master Paradigm" to list exactly what forms are missing for each lemma.

### Phase 2: FST Grammar Development
* **Lexicon Layer:** Define the roots and valid binyanim based on Phase 1.
* **Morphotactic Layer:** Define the order of morphemes: `[Preposition] + [Article] + [Base Form] + [Pronominal Suffix]`.
* **Phonological Layer:** A series of cascading transducers to handle:
    1.  Vowel reduction (e.g., *Qamets* to *Shewa*).
    2.  Daghesh placement (Lene and Forte).
    3.  Guttural preferences.

### Phase 3: Generation & Export
* **Bidirectional Testing:** Ensure the FST can take a surface form (e.g., *v’ha-mela-khim*) and return the lemma/analysis, and vice versa.
* **Lookup Table Creation:** Iterate through every root/stem combination and generate every possible valid permutation (with and without affixes).
* **Output:** Export to a massive CSV or SQLite database for use in other applications.

---

## 4. Technical Constraints
* **Tooling:** Recommended use of `Foma`, `HFST` (Helsinki Finite-State Technology), or a Python-based FST library like `Pynini`.
* **Performance:** Runtime speed is secondary to accuracy. The final artifact is the generated table, not a real-time engine.
* **Normalization:** All forms must be generated with full Niqqud (vocalization).
