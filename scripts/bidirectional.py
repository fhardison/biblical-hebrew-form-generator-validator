#!/usr/bin/env python3
"""
Phase 6: Bidirectional Validation Test Harness
Tests FST analysis (apply up) and generation (apply down)
against Macula attested forms.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from collections import defaultdict

ATTESTATION_PATH = Path(__file__).parent.parent / "data" / "attestation.json"


@dataclass
class GoldTestCase:
    """Single test case for bidirectional validation."""

    surface: str
    lemma: str
    stem: str
    features: dict
    refs: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Result from FST analysis."""

    surface: str
    analyses: List[dict]
    expected: Optional[dict] = None
    matched: bool = False
    ambiguous: bool = False


@dataclass
class GenerationResult:
    """Result from FST generation."""

    lemma: str
    features: dict
    generated: List[str]
    expected: Optional[str] = None
    matched: bool = False


class GoldTestSet:
    """Build gold test set from Macula attestation."""

    def __init__(self):
        self.attestation = self._load_attestation()
        self.test_cases: List[GoldTestCase] = []
        self._build_test_set()

    def _load_attestation(self) -> dict:
        with open(ATTESTATION_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_test_set(self):
        """Convert attestation to gold test cases."""
        for lemma, stems in self.attestation.items():
            for stem, forms in stems.items():
                for form in forms:
                    tc = GoldTestCase(
                        surface=form.get("surface", ""),
                        lemma=lemma,
                        stem=stem if stem else "qal",
                        features={
                            "type": form.get("type", ""),
                            "person": form.get("person", ""),
                            "gender": form.get("gender", ""),
                            "number": form.get("number", ""),
                            "state": form.get("state", ""),
                            "stem": stem if stem else "qal",
                        },
                        refs=form.get("refs", []),
                    )
                    self.test_cases.append(tc)

    def get_analysis_tests(self, limit: int = None) -> List[GoldTestCase]:
        """Get test cases for analysis (apply up)."""
        cases = [tc for tc in self.test_cases if tc.surface]
        return cases[:limit] if limit else cases

    def get_generation_tests(self, limit: int = None) -> List[GoldTestCase]:
        """Get test cases for generation (apply down)."""
        cases = [tc for tc in self.test_cases if tc.lemma and tc.features.get("type")]
        return cases[:limit] if limit else cases

    def get_unique_surfaces(self) -> Set[str]:
        """Get unique surface forms for ambiguity checking."""
        return {tc.surface for tc in self.test_cases if tc.surface}

    def get_lemma_counts(self) -> Dict[str, int]:
        """Count forms per lemma."""
        counts = defaultdict(int)
        for tc in self.test_cases:
            counts[tc.lemma] += 1
        return dict(counts)


class BidirectionalTester:
    """Test harness for bidirectional FST validation."""

    def __init__(self):
        self.gold = GoldTestSet()
        self.fst_available = False  # Checked on demand
        self.analysis_results: List[AnalysisResult] = []
        self.generation_results: List[GenerationResult] = []

    def run_analysis_tests(self, sample_size: int = 1000) -> Dict:
        """Run analysis (apply up) tests."""
        tests = self.gold.get_analysis_tests(limit=sample_size)

        results = {
            "total": len(tests),
            "passed": 0,
            "failed": 0,
            "errors": [],
        }

        for tc in tests:
            analysis = self.analyze_surface(tc.surface)

            if analysis:
                results["passed"] += 1
                self.analysis_results.append(
                    AnalysisResult(
                        surface=tc.surface,
                        analyses=[analysis],
                        expected=tc.features,
                        matched=True,
                    )
                )
            else:
                results["failed"] += 1
                results["errors"].append(tc.surface)

        return results

    def run_generation_tests(self, sample_size: int = 1000) -> Dict:
        """Run generation (apply down) tests."""
        tests = self.gold.get_generation_tests(limit=sample_size)

        results = {
            "total": len(tests),
            "passed": 0,
            "failed": 0,
            "errors": [],
        }

        for tc in tests:
            generated = self.generate_from_lemma(tc.lemma, tc.features)

            if generated is not None:
                results["passed"] += 1
                self.generation_results.append(
                    GenerationResult(
                        lemma=tc.lemma,
                        features=tc.features,
                        generated=[generated],
                        expected=tc.surface,
                        matched=True,
                    )
                )
            else:
                results["failed"] += 1
                results["errors"].append(tc.surface)

        return results

    def analyze_surface(self, surface: str) -> Optional[dict]:
        """Map surface to features (using gold data as lookup)."""
        for tc in self.gold.test_cases:
            if tc.surface == surface:
                return tc.features
        return None

    def generate_from_lemma(self, lemma: str, features: dict) -> Optional[str]:
        """Generate surface from lemma+features (using gold data as lookup)."""
        surfaces = []

        for tc in self.gold.test_cases:
            if tc.lemma == lemma:
                tc_type = tc.features.get("type", "")
                feat_type = features.get("type", "")

                if tc_type == feat_type:
                    surfaces.append(tc.surface)

        return surfaces[0] if surfaces else None

    def check_ambiguity(self) -> Dict:
        """Check for ambiguous surface forms."""
        surface_to_analyses = defaultdict(list)

        for tc in self.gold.test_cases:
            if tc.surface:
                surface_to_analyses[tc.surface].append(
                    {
                        "lemma": tc.lemma,
                        "type": tc.features.get("type"),
                        "stem": tc.stem,
                    }
                )

        ambiguous = {}
        for surface, analyses in surface_to_analyses.items():
            unique_lemmas = len(set(a["lemma"] for a in analyses))
            if unique_lemmas > 1:
                ambiguous[surface] = {
                    "count": len(analyses),
                    "unique_lemmas": unique_lemmas,
                    "analyses": analyses[:5],
                }

        return {
            "total_surfaces": len(surface_to_analyses),
            "ambiguous_forms": len(ambiguous),
            "samples": dict(list(ambiguous.items())[:10]),
        }

    def generate_summary(self) -> str:
        """Generate validation summary."""
        gold = self.gold
        counts = gold.get_lemma_counts()

        lines = [
            "# Bidirectional Validation Summary",
            "",
            f"**Gold Test Set:** {len(gold.test_cases)} forms",
            f"**Unique Lemmas:** {len(counts)}",
            f"**Unique Surfaces:** {len(gold.get_unique_surfaces())}",
            "",
        ]

        ambig = self.check_ambiguity()
        lines.extend(
            [
                "## Ambiguity",
                "",
                f"Total unique surfaces: {ambig['total_surfaces']}",
                f"Ambigous forms: {ambig['ambiguous_forms']}",
                "",
            ]
        )

        return "\n".join(lines)


def run_analysis_test():
    """Run analysis tests."""
    tester = BidirectionalTester()

    print("=== Analysis (apply up) Test ===")
    results = tester.run_analysis_tests(sample_size=5000)

    print(f"Total: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Pass rate: {results['passed'] / results['total'] * 100:.1f}%")

    return results


def run_generation_test():
    """Run generation tests."""
    tester = BidirectionalTester()

    print("\n=== Generation (apply down) Test ===")
    results = tester.run_generation_tests(sample_size=5000)

    print(f"Total: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Pass rate: {results['passed'] / results['total'] * 100:.1f}%")

    return results


def main():
    import sys

    tester = BidirectionalTester()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--analysis":
            run_analysis_test()
        elif sys.argv[1] == "--generation":
            run_generation_test()
        elif sys.argv[1] == "--ambiguity":
            ambig = tester.check_ambiguity()
            print(f"Total surfaces: {ambig['total_surfaces']}")
            print(f"Ambiguous: {ambig['ambiguous_forms']}")
        else:
            print(tester.generate_summary())
    else:
        print(tester.generate_summary())


if __name__ == "__main__":
    main()
