"""
Unit tests for Phase 5 validation harness
Run with: python -m pytest tests/test_validate.py -v
"""

import pytest
from scripts.validate import (
    ValidationHarness,
    CoverageStats,
    ValidationResult,
)


class TestValidationHarness:
    def test_harness_initializes(self):
        harness = ValidationHarness()
        assert harness is not None
        assert harness.attestation is not None
        assert harness.paradigm is not None

    def test_loads_attestation_data(self):
        harness = ValidationHarness()
        assert len(harness.attestation) > 0

    def test_loads_paradigm(self):
        harness = ValidationHarness()
        assert "stems" in harness.paradigm
        assert "verb_conjugations" in harness.paradigm

    def test_run_coverage_qal(self):
        harness = ValidationHarness()
        stats = harness.run_coverage(stem_filter="qal")
        assert stats.total_forms > 0
        assert stats.total_forms == stats.matched + stats.unmatched

    def test_run_coverage_all(self):
        harness = ValidationHarness()
        stats = harness.run_coverage()
        assert stats.total_forms > 30000
        assert stats.matched > 0

    def test_by_stem_populated(self):
        harness = ValidationHarness()
        stats = harness.run_coverage()
        assert "qal" in stats.by_stem


class TestCoverageStats:
    def test_initializes_empty(self):
        stats = CoverageStats()
        assert stats.total_forms == 0
        assert stats.matched == 0

    def test_accumulates_counts(self):
        stats = CoverageStats()
        stats.total_forms = 100
        stats.matched = 95
        stats.unmatched = 5
        assert stats.matched + stats.unmatched == stats.total_forms


class TestValidationResult:
    def test_initializes(self):
        result = ValidationResult(
            lemma="בָּרָא",
            stem="qal",
            surface="בָּרָא",
            expected_features={"type": "qatal", "person": "third"},
        )
        assert result.lemma == "בָּרָא"
        assert result.stem == "qal"
        assert result.surface == "בָּרָא"


class TestParadigmMapping:
    def test_validates_qatal(self):
        harness = ValidationHarness()
        form = {
            "type": "qatal",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        assert harness._validate_verb(form, "qal") is True

    def test_validates_yiqtol(self):
        harness = ValidationHarness()
        form = {
            "type": "yiqtol",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        assert harness._validate_verb(form, "qal") is True

    def test_validates_imperative(self):
        harness = ValidationHarness()
        form = {
            "type": "imperative",
            "person": "second",
            "gender": "masculine",
            "number": "singular",
        }
        assert harness._validate_verb(form, "qal") is True

    def test_validates_infinitive(self):
        harness = ValidationHarness()
        form = {
            "type": "infinitive construct",
            "person": "",
            "gender": "",
            "number": "",
        }
        assert harness._validate_verb(form, "qal") is True

    def test_validates_jussive_3rd(self):
        harness = ValidationHarness()
        form = {
            "type": "jussive",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        assert harness._validate_verb(form, "qal") is True

    def test_validates_jussive_2nd(self):
        harness = ValidationHarness()
        form = {
            "type": "jussive",
            "person": "second",
            "gender": "masculine",
            "number": "singular",
        }
        assert harness._validate_verb(form, "qal") is True

    def test_rejects_imperative_3rd_person(self):
        harness = ValidationHarness()
        form = {
            "type": "imperative",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        assert harness._validate_verb(form, "qal") is False

    def test_validates_noun(self):
        harness = ValidationHarness()
        form = {
            "type": "common",
            "gender": "masculine",
            "number": "singular",
            "state": "absolute",
        }
        assert harness._validate_noun(form) is True

    def test_validates_noun_plural(self):
        harness = ValidationHarness()
        form = {
            "type": "common",
            "gender": "masculine",
            "number": "plural",
            "state": "absolute",
        }
        assert harness._validate_noun(form) is True

    def test_validates_noun_construct(self):
        harness = ValidationHarness()
        form = {
            "type": "common",
            "gender": "masculine",
            "number": "singular",
            "state": "construct",
        }
        assert harness._validate_noun(form) is True


class TestReportGeneration:
    def test_generate_report_runs(self):
        harness = ValidationHarness()
        harness.run_coverage(stem_filter="qal")
        report = harness.generate_report()
        assert "Coverage Report" in report
        assert "Qal" in report or "qal" in report
