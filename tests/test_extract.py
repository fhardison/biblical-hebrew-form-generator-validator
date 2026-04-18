"""
Unit tests for scripts/extract.py
Run with: python -m pytest tests/test_extract.py -v
"""

from pathlib import Path

from extract import (
    VERB_PARADIGM,
    VERB_PARADIGM_SET,
    _cell,
    cell_id,
    classify_root,
    features_to_cell,
    parse_word_groups,
    row_to_features,
    strip_diacritics,
)


# ─── strip_diacritics ────────────────────────────────────────────────────────


class TestStripDiacritics:
    def test_strips_vowel_points(self):
        # בָּרָא (bara) → ברא
        assert strip_diacritics("בָּרָא") == "ברא"

    def test_strips_cantillation(self):
        # Text with a tiphcha (U+05A3) over the aleph
        text_with_tiphcha = "בָּרָ֣א"
        assert strip_diacritics(text_with_tiphcha) == "ברא"

    def test_plain_text_unchanged(self):
        assert strip_diacritics("ברא") == "ברא"

    def test_empty_string(self):
        assert strip_diacritics("") == ""

    def test_strips_shewa(self):
        # בְּ (be-) → ב
        assert strip_diacritics("בְּ") == "ב"

    def test_strips_hateph(self):
        # אֱלֹהִים → אלהים
        assert strip_diacritics("אֱלֹהִים") == "אלהים"

    def test_non_hebrew_ascii_unchanged(self):
        assert strip_diacritics("hello") == "hello"


# ─── classify_root ────────────────────────────────────────────────────────────


class TestClassifyRoot:
    # ── Strong ───────────────────────────────────────────────────────────────

    def test_strong_root(self):
        # כָּתַב (ktb) = strong
        assert classify_root("כָּתַב") == ["strong"]

    def test_strong_qatal_form(self):
        # פָּקַד (pqd) — pe, qoph, dalet; none are gutturals
        assert classify_root("פָּקַד") == ["strong"]

    # ── I-class ──────────────────────────────────────────────────────────────

    def test_I_aleph(self):
        # אָמַר (ʾmr) → I-aleph
        result = classify_root("אָמַר")
        assert "I-aleph" in result

    def test_I_nun(self):
        # נָפַל (npl) → I-nun
        result = classify_root("נָפַל")
        assert "I-nun" in result

    def test_I_waw(self):
        # וָלַד (wld) → I-waw  (rare; most I-waw lemmas show as yod in BH)
        result = classify_root("וָלַד")
        assert "I-waw" in result

    def test_I_yod(self):
        # יָצָא (yṣʾ) → I-yod
        result = classify_root("יָצָא")
        assert "I-yod" in result

    def test_I_guttural_het(self):
        # חָלַק (ḥlq) → I-guttural
        result = classify_root("חָלַק")
        assert "I-guttural" in result

    def test_I_guttural_ayin(self):
        # עָמַד (ʿmd) → I-guttural
        result = classify_root("עָמַד")
        assert "I-guttural" in result

    # ── II / Hollow ───────────────────────────────────────────────────────────

    def test_hollow_waw(self):
        # שׁוּב (šwb) → hollow
        result = classify_root("שׁוּב")
        assert "hollow" in result

    def test_hollow_yod(self):
        # שִׂים (śym) → hollow
        result = classify_root("שִׂים")
        assert "hollow" in result

    def test_II_guttural(self):
        # בֵּרַךְ (brk with ayin as C2 — use שָׁאַל sʾl instead)
        # שָׁאַל (šʾl) → II-guttural (aleph is a guttural)
        result = classify_root("שָׁאַל")
        assert "II-guttural" in result

    # ── III-class ─────────────────────────────────────────────────────────────

    def test_III_he(self):
        # בָּנָה (bnh) → III-he
        result = classify_root("בָּנָה")
        assert "III-he" in result

    def test_III_aleph(self):
        # מָצָא (mṣʾ) → III-aleph
        result = classify_root("מָצָא")
        assert "III-aleph" in result

    def test_III_guttural_het(self):
        # שָׁלַח (šlḥ) → III-guttural
        result = classify_root("שָׁלַח")
        assert "III-guttural" in result

    # ── Geminate ─────────────────────────────────────────────────────────────

    def test_geminate(self):
        # סָבַב (sbb) → geminate
        result = classify_root("סָבַב")
        assert "geminate" in result

    # ── Doubly-weak ───────────────────────────────────────────────────────────

    def test_doubly_weak_has_multiple_tags(self):
        # הָיָה (hyh) = I-guttural/I-he + III-he + hollow-ish → doubly-weak
        result = classify_root("הָיָה")
        assert "doubly-weak" in result
        assert len(result) > 2  # at least two primary tags + doubly-weak

    def test_I_aleph_plus_III_he_is_doubly_weak(self):
        # אָבָה (ʾbh) → I-aleph + III-he → doubly-weak
        result = classify_root("אָבָה")
        assert "I-aleph" in result
        assert "III-he" in result
        assert "doubly-weak" in result

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_empty_string_returns_unknown(self):
        assert classify_root("") == ["unknown"]

    def test_single_consonant_classifies_c1(self):
        # A lone aleph has no C2/C3; the function classifies what it can (C1).
        # This is a pathological input but should not raise an exception.
        result = classify_root("א")
        assert "I-aleph" in result
        assert "doubly-weak" not in result


# ─── cell_id ─────────────────────────────────────────────────────────────────


class TestCellId:
    def test_finite_verb_cell(self):
        c = _cell("qatal", "third", "masculine", "singular")
        assert cell_id(c) == "qatal.third.masculine.singular"

    def test_infinitive_cell(self):
        c = _cell("infinitive construct")
        assert cell_id(c) == "infinitive construct"

    def test_participle_cell(self):
        c = _cell("participle active", "", "masculine", "singular", "absolute")
        assert cell_id(c) == "participle active.masculine.singular.absolute"

    def test_imperative_cell(self):
        c = _cell("imperative", "second", "feminine", "plural")
        assert cell_id(c) == "imperative.second.feminine.plural"


# ─── features_to_cell ────────────────────────────────────────────────────────


class TestFeaturesToCell:
    def _make_features(self, type_, person="", gender="", number="", state=""):
        return {
            "type": type_, "person": person, "gender": gender,
            "number": number, "state": state, "morph": "",
        }

    def test_qatal_3ms(self):
        f = self._make_features("qatal", "third", "masculine", "singular")
        assert features_to_cell(f) == _cell("qatal", "third", "masculine", "singular")

    def test_yiqtol_1cp(self):
        f = self._make_features("yiqtol", "first", "common", "plural")
        assert features_to_cell(f) == _cell("yiqtol", "first", "common", "plural")

    def test_participle_active(self):
        f = self._make_features("participle active", "", "feminine", "singular", "absolute")
        assert features_to_cell(f) == _cell("participle active", "", "feminine", "singular", "absolute")

    def test_infinitive_construct(self):
        f = self._make_features("infinitive construct")
        assert features_to_cell(f) == _cell("infinitive construct")

    def test_unknown_type_passes_through(self):
        f = self._make_features("unknown_type", "first", "common", "singular")
        result = features_to_cell(f)
        assert result[0] == "unknown_type"

    def test_in_paradigm_set(self):
        f = self._make_features("wayyiqtol", "third", "masculine", "singular")
        assert features_to_cell(f) in VERB_PARADIGM_SET


# ─── row_to_features ─────────────────────────────────────────────────────────


class TestRowToFeatures:
    def _make_row(self, **kwargs):
        defaults = {
            "type": "", "person": "", "gender": "",
            "number": "", "state": "", "morph": "",
        }
        defaults.update(kwargs)
        return defaults

    def test_extracts_all_fields(self):
        row = self._make_row(
            type="qatal", person="third", gender="masculine",
            number="singular", state="", morph="Vqp3ms",
        )
        result = row_to_features(row)
        assert result == {
            "type": "qatal", "person": "third", "gender": "masculine",
            "number": "singular", "state": "", "morph": "Vqp3ms",
        }

    def test_empty_fields_preserved(self):
        row = self._make_row(type="infinitive construct", morph="Vqc")
        result = row_to_features(row)
        assert result["person"] == ""
        assert result["state"] == ""


# ─── VERB_PARADIGM integrity ─────────────────────────────────────────────────


class TestVerbParadigm:
    def test_no_duplicate_cells(self):
        assert len(VERB_PARADIGM) == len(VERB_PARADIGM_SET)

    def test_contains_qatal_3ms(self):
        assert _cell("qatal", "third", "masculine", "singular") in VERB_PARADIGM_SET

    def test_contains_infinitive_construct(self):
        assert _cell("infinitive construct") in VERB_PARADIGM_SET

    def test_contains_infinitive_absolute(self):
        assert _cell("infinitive absolute") in VERB_PARADIGM_SET

    def test_imperative_has_no_third_person(self):
        third_person_imperatives = [
            c for c in VERB_PARADIGM
            if c[0] == "imperative" and c[1] == "third"
        ]
        assert third_person_imperatives == []

    def test_imperative_has_no_first_person(self):
        first_person_imperatives = [
            c for c in VERB_PARADIGM
            if c[0] == "imperative" and c[1] == "first"
        ]
        assert first_person_imperatives == []

    def test_each_cell_is_five_tuple(self):
        for cell in VERB_PARADIGM:
            assert len(cell) == 5

    def test_paradigm_has_expected_count(self):
        # 9 qatal + 10 yiqtol + 10 wayyiqtol + 9 weqatal + 8 jussive
        # + 2 cohortative + 4 imperative + 8 ptcp-act + 5 ptcp-pass
        # + 1 inf-cstr + 1 inf-abs = 67
        assert len(VERB_PARADIGM) == 67


# ─── parse_word_groups ────────────────────────────────────────────────────────

# Minimal TSV header used in fake-file tests
_HEADER = "\t".join([
    "xml:id", "ref", "class", "text", "transliteration", "after",
    "strongnumberx", "stronglemma", "sensenumber", "greek", "greekstrong",
    "gloss", "english", "mandarin", "stem", "morph", "lang", "lemma",
    "pos", "person", "gender", "number", "state", "type",
    "lexdomain", "contextualdomain", "coredomain", "sdbh", "extends",
    "frame", "subjref", "participantref",
])


def _make_tsv_row(overrides: dict | None = None, **kwargs) -> str:
    """Return a single TSV data row with sensible defaults.

    Pass fields with colons in their names (e.g. ``xml:id``) via the
    *overrides* dict, since colons are illegal in Python keyword arguments.
    """
    defaults = {
        "xml:id": "o010010010011", "ref": "GEN 1:1!1", "class": "verb",
        "text": "בָּרָא", "transliteration": "", "after": " ",
        "strongnumberx": "1254", "stronglemma": "בָּרָא", "sensenumber": "1",
        "greek": "", "greekstrong": "", "gloss": "", "english": "",
        "mandarin": "", "stem": "qal", "morph": "Vqp3ms", "lang": "H",
        "lemma": "בָּרָא", "pos": "verb", "person": "third",
        "gender": "masculine", "number": "singular", "state": "",
        "type": "qatal", "lexdomain": "", "contextualdomain": "",
        "coredomain": "", "sdbh": "", "extends": "", "frame": "",
        "subjref": "", "participantref": "",
    }
    defaults.update(kwargs)
    if overrides:
        defaults.update(overrides)
    # Preserve header column order
    cols = _HEADER.split("\t")
    return "\t".join(defaults[c] for c in cols)


def _tsv_file(*rows: str, tmp_path) -> Path:
    """Write a TSV file with header + given rows and return its path."""
    content = _HEADER + "\n" + "\n".join(rows) + "\n"
    p = tmp_path / "test.tsv"
    p.write_text(content, encoding="utf-8")
    return p


class TestParseWordGroups:
    def test_simple_verb_group(self, tmp_path):
        path = _tsv_file(
            _make_tsv_row(ref="GEN 1:1!1"),
            tmp_path=tmp_path,
        )
        groups = list(parse_word_groups(path))
        assert len(groups) == 1
        assert groups[0]["head"]["lemma"] == "בָּרָא"
        assert groups[0]["prefixes"] == []
        assert groups[0]["suffix"] is None

    def test_conjunction_clitic_grouped_with_verb(self, tmp_path):
        """Conjunction and verb share the same ref → conjunction is a prefix."""
        path = _tsv_file(
            _make_tsv_row(
                {"xml:id": "o010010010011"},
                ref="GEN 1:1!1",
                text="וַ", morph="C", pos="conjunction",
                lemma="וְ", stem="", type="", person="",
                gender="", number="", state="",
            ),
            _make_tsv_row(
                {"xml:id": "o010010010012"},
                ref="GEN 1:1!1",
                text="יֹּאמֶר", morph="Vqw3ms", pos="verb",
                lemma="אָמַר", stem="qal", type="wayyiqtol",
                person="third", gender="masculine", number="singular",
            ),
            tmp_path=tmp_path,
        )
        groups = list(parse_word_groups(path))
        assert len(groups) == 1
        wg = groups[0]
        assert wg["head"]["lemma"] == "אָמַר"
        assert len(wg["prefixes"]) == 1
        assert wg["prefixes"][0]["morph"] == "C"
        assert wg["surface"] == "וַיֹּאמֶר"

    def test_pronominal_suffix_captured(self, tmp_path):
        """Suffix token sharing a ref is captured as the suffix."""
        path = _tsv_file(
            _make_tsv_row(
                {"xml:id": "o010010110131"},
                ref="GEN 1:11!13",
                text="לְ", morph="R", pos="preposition",
                lemma="לְ", stem="", type="", person="",
                gender="", number="", state="",
            ),
            _make_tsv_row(
                {"xml:id": "o010010110132"},
                ref="GEN 1:11!13",
                text="מִינ", morph="Ncmsc", pos="noun",
                lemma="מִין", stem="", type="common",
                person="", gender="masculine", number="singular", state="construct",
            ),
            _make_tsv_row(
                {"xml:id": "o010010110133"},
                ref="GEN 1:11!13",
                text="וֹ", morph="Sp3ms", pos="suffix",
                lemma="הוּא", stem="", type="pronominal",
                person="third", gender="masculine", number="singular", state="",
            ),
            tmp_path=tmp_path,
        )
        groups = list(parse_word_groups(path))
        assert len(groups) == 1
        wg = groups[0]
        assert wg["head"]["lemma"] == "מִין"
        assert wg["suffix"] is not None
        assert wg["suffix"]["morph"] == "Sp3ms"
        assert wg["surface"] == "לְמִינוֹ"

    def test_word_group_without_head_is_skipped(self, tmp_path):
        """A word position with only a preposition and no noun/verb is dropped."""
        path = _tsv_file(
            _make_tsv_row(
                ref="GEN 1:1!1", text="בְּ", morph="R",
                pos="preposition", lemma="בְּ", stem="",
                type="", person="", gender="", number="", state="",
            ),
            tmp_path=tmp_path,
        )
        groups = list(parse_word_groups(path))
        assert groups == []

    def test_two_separate_words_produce_two_groups(self, tmp_path):
        path = _tsv_file(
            _make_tsv_row({"xml:id": "o010010010011"}, ref="GEN 1:1!1"),
            _make_tsv_row(
                {"xml:id": "o010010010021"},
                ref="GEN 1:1!2",
                text="אֱלֹהִים", morph="Ncmpa", pos="noun",
                lemma="אֱלֹהִים", stem="", type="common",
                person="", gender="masculine", number="plural",
                state="absolute",
            ),
            tmp_path=tmp_path,
        )
        groups = list(parse_word_groups(path))
        assert len(groups) == 2

    def test_aramaic_rows_still_yielded(self, tmp_path):
        """parse_word_groups yields all head-bearing groups; lang filtering
        happens in build_catalogs, not here."""
        path = _tsv_file(
            _make_tsv_row(ref="DAN 2:4!1", lang="A",
                          text="מַלְכָּא", morph="Ncmsa", pos="noun",
                          lemma="מֶלֶךְ", stem="", type="common",
                          person="", gender="masculine", number="singular",
                          state="absolute"),
            tmp_path=tmp_path,
        )
        groups = list(parse_word_groups(path))
        assert len(groups) == 1
        assert groups[0]["head"]["lang"] == "A"
