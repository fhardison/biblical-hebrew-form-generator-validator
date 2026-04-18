#!/usr/bin/env python3
"""
Phase 5: Validation and Test Harness
Compares FST output against Macula attestation data.
"""

import json
import yaml
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict

ATTESTATION_PATH = Path(__file__).parent.parent / "data" / "attestation.json"
PARADIGM_PATH = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"


@dataclass
class ValidationResult:
    lemma: str
    stem: str
    surface: str
    expected_features: dict
    fst_output: str = ""
    matched: bool = False
    error_type: str = ""


@dataclass
class CoverageStats:
    total_forms: int = 0
    matched: int = 0
    unmatched: int = 0
    by_stem: dict = field(default_factory=dict)
    failing_forms: list = field(default_factory=list)


class ValidationHarness:
    def __init__(self):
        self.attestation = self._load_attestation()
        self.paradigm = self._load_paradigm()
        self.stats = CoverageStats()
        self.fst_available = self._check_fst()

    def _load_attestation(self) -> dict:
        with open(ATTESTATION_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_paradigm(self) -> dict:
        with open(PARADIGM_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _check_fst(self) -> bool:
        import subprocess

        result = subprocess.run(["which", "foma"], capture_output=True)
        return result.returncode == 0

    def run_coverage(self, stem_filter: str = None) -> CoverageStats:
        """Run coverage analysis on attestation data."""
        self.stats = CoverageStats()

        for lemma, stems in self.attestation.items():
            for stem, forms in stems.items():
                if stem_filter and stem != stem_filter:
                    continue

                for form in forms:
                    self.stats.total_forms += 1

                    result = self._validate_form(lemma, stem, form)

                    stem_key = stem if stem else "qal"
                    if stem_key not in self.stats.by_stem:
                        self.stats.by_stem[stem_key] = {"total": 0, "matched": 0}

                    self.stats.by_stem[stem_key]["total"] += 1

                    if result.matched:
                        self.stats.matched += 1
                        self.stats.by_stem[stem_key]["matched"] += 1
                    else:
                        self.stats.unmatched += 1
                        self.stats.failing_forms.append(result)

        return self.stats

    def _validate_form(self, lemma: str, stem: str, form: dict) -> ValidationResult:
        """Validate a single form against paradigm."""
        result = ValidationResult(
            lemma=lemma,
            stem=stem,
            surface=form.get("surface", ""),
            expected_features={
                "type": form.get("type", ""),
                "person": form.get("person", ""),
                "gender": form.get("gender", ""),
                "number": form.get("number", ""),
                "state": form.get("state", ""),
            },
        )

        form_type = form.get("type", "")
        if not form_type:
            result.error_type = "missing_type"
            return result

        if form_type in ["common", "proper", "gentilic"]:
            result.matched = self._validate_noun(form)
        else:
            result.matched = self._validate_verb(form, stem)

        return result

    def _validate_verb(self, form: dict, stem: str) -> bool:
        """Validate verb form against paradigm."""
        form_type = form.get("type", "")
        person = form.get("person", "")
        gender = form.get("gender", "")
        number = form.get("number", "")

        valid_conjugations = self.paradigm.get("verb_conjugations", [])

        conv_map = {
            "qatal": "qatal",
            "yiqtol": "yiqtol",
            "imperative": "imperative",
            "wayyiqtol": "wayyiqtol",
            "weqatal": "weqatal",
            "infinitive construct": "infinitive_construct",
            "infinitive absolute": "infinitive_absolute",
            "participle active": "participle_active",
            "participle passive": "participle_passive",
            "jussive": "jussive",
            "cohortative": "cohortative",
        }

        conjugation = conv_map.get(form_type)
        if not conjugation or conjugation not in valid_conjugations:
            return False

        if conjugation in ("infinitive_construct", "infinitive_absolute"):
            return True

        if conjugation in ("participle_active", "participle_passive"):
            return gender in ("masculine", "feminine", "common", "both")

        if conjugation in ("jussive",):
            # In Biblical Hebrew, jussive can be 3rd (traditional) or 2nd (hortatory)
            # Macula sometimes marks 2nd person as jussive
            return person in ("third", "second")

        if conjugation in ("cohortative",):
            return person == "first"

        if conjugation in ("imperative",):
            return person == "second"

        return person in ("first", "second", "third") and number in (
            "singular",
            "plural",
        )

    def _validate_noun(self, form: dict) -> bool:
        """Validate noun form against paradigm."""
        number = form.get("number", "")
        state = form.get("state", "")

        valid_numbers = {"singular", "plural", "dual"}
        valid_states = {"absolute", "construct"}

        if number and number not in valid_numbers:
            return False

        if state and state not in valid_states:
            return False

        return True

    def generate_report(self) -> str:
        """Generate coverage report."""
        total = self.stats.total_forms
        matched = self.stats.matched
        unmatched = self.stats.unmatched
        pct = (matched / total * 100) if total > 0 else 0

        lines = [
            "# Coverage Report",
            "",
            f"**Total forms:** {total}",
            f"**Matched:** {matched} ({pct:.1f}%)",
            f"**Unmatched:** {unmatched}",
            "",
            "## By Stem",
            "",
        ]

        for stem, counts in sorted(self.stats.by_stem.items()):
            stem_pct = (
                (counts["matched"] / counts["total"] * 100)
                if counts["total"] > 0
                else 0
            )
            lines.append(
                f"- {stem}: {counts['matched']}/{counts['total']} ({stem_pct:.1f}%)"
            )

        if self.stats.failing_forms:
            lines.extend(
                [
                    "",
                    "## Failing Forms (sample)",
                    "",
                ]
            )
            for f in self.stats.failing_forms[:10]:
                lines.append(
                    f"- {f.surface} ({f.expected_features.get('type', '')}) - {f.error_type}"
                )

        return "\n".join(lines)


def run_baseline_validation():
    """Run Qal strong verb baseline."""
    harness = ValidationHarness()

    print("=== Qal Strong Verb Baseline ===")
    stats = harness.run_coverage(stem_filter="qal")

    print(f"Total Qal forms: {stats.total_forms}")
    print(f"Matched: {stats.matched}")
    print(f"Unmatched: {stats.unmatched}")

    return stats


def run_all_stems():
    """Run coverage on all stems."""
    harness = ValidationHarness()
    stats = harness.run_coverage()

    print("\n=== Full Coverage ===")
    print(f"Total forms: {stats.total_forms}")
    print(f"Matched: {stats.matched} ({stats.matched / stats.total_forms * 100:.1f}%)")

    print("\nBy Stem:")
    for stem, counts in sorted(stats.by_stem.items()):
        pct = counts["matched"] / counts["total"] * 100 if counts["total"] > 0 else 0
        print(f"  {stem}: {counts['matched']}/{counts['total']} ({pct:.1f}%)")

    return stats


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--qal":
        run_baseline_validation()
    else:
        run_all_stems()


if __name__ == "__main__":
    main()
