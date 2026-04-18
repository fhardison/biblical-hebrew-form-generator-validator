"""
Unit tests for HebrewFST wrapper.
Run: python -m pytest tests/test_hebrew_fst.py -v
"""

import pytest
from scripts.hebrew_fst import HebrewFST, Analysis


class TestHebrewFST:
    def setup_method(self):
        self.fst = HebrewFST()

    def teardown_method(self):
        self.fst.close()

    def test_initialization(self):
        assert self.fst is not None
        assert len(self.fst.stems) > 0
        assert len(self.fst.vtypes) > 0

    def test_stems_include_qal(self):
        assert "qal" in self.fst.stems

    def test_vtypes_include_qatal(self):
        assert "qatal" in self.fst.vtypes

    def test_analyze_returns_list(self):
        result = self.fst.analyze("אֱלֹהִים")
        assert isinstance(result, list)

    def test_generate_returns_list(self):
        result = self.fst.generate("בָּרָא", "qal", "qatal")
        assert isinstance(result, list)

    def test_get_lemma_forms(self):
        result = self.fst.get_lemma_forms("אֱלֹהִים")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_stem_forms(self):
        result = self.fst.get_stem_forms("qal")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_pattern(self):
        result = self.fst.search("אֱל*")
        assert isinstance(result, list)

    def test_conjugation_paradigm(self):
        result = self.fst.get_conjugation_paradigm("הָיָה", "qal")
        assert isinstance(result, dict)
        assert "qatal" in result

    def test_context_manager(self):
        with HebrewFST() as fst:
            assert fst is not None
            stems = fst.stems
            assert "qal" in stems


class TestAnalysis:
    def test_create_analysis(self):
        a = Analysis(
            surface="בָּרָא",
            lemma="בָּרָא",
            stem="qal",
            cell_id="qal.qatal.3ms",
            vtype="qatal",
            person="third",
            gender="masculine",
            number="singular",
            state="",
            pron_suffix="",
        )
        assert a.surface == "בָּרָא"
        assert a.lemma == "בָּרָא"

    def test_analysis_str(self):
        a = Analysis(
            surface="בָּרָא",
            lemma="בָּרָא",
            stem="qal",
            cell_id="qal.qatal.3ms",
            vtype="qatal",
            person="third",
            gender="masculine",
            number="singular",
            state="",
            pron_suffix="",
        )
        assert "בָּרָא" in str(a)
        assert "qal" in str(a)


class TestValidate:
    def setup_method(self):
        self.fst = HebrewFST()

    def teardown_method(self):
        self.fst.close()

    def test_validate_attested_qal(self):
        result = self.fst.validate("בָּרָא", "בָּרָא", "qal")
        assert result is True

    def test_validate_attested_any_stem(self):
        result = self.fst.validate("בָּרָא", "בָּרָא")
        assert result is True

    def test_validate_nonexistent_lemma(self):
        result = self.fst.validate("בָּרָא", "לא קיים", "qal")
        assert result is False


class TestDatabase:
    def test_database_exists(self):
        import os

        assert os.path.exists("output/forms.sqlite")

    def test_database_has_data(self):
        import sqlite3

        conn = sqlite3.connect("output/forms.sqlite")
        count = conn.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
        assert count > 30000
