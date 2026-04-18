#!/usr/bin/env python3
"""
Paradigm validation: maps Macula forms to cell_IDs using master_paradigm.yaml
Handles pronominal suffixes, possessive suffixes, and proclitics.
"""

import json
import yaml
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

PARADIGM_PATH = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
ATTESTATION_PATH = Path(__file__).parent.parent / "data" / "attestation.json"


type_to_conjugation = {
    "qatal": "qatal",
    "wayyiqtol": "wayyiqtol",
    "weqatal": "weqatal",
    "yiqtol": "yiqtol",
    "imperative": "imperative",
    "infinitive construct": "infinitive_construct",
    "infinitive absolute": "infinitive_absolute",
    "participle active": "participle_active",
    "participle passive": "participle_passive",
    "jussive": "jussive",
    "cohortative": "cohortative",
}

noun_types = {"common", "proper", "gentilic"}

default_stems = {
    "qal": "qal",
    "niphal": "niphal",
    "piel": "piel",
    "pual": "pual",
    "hiphil": "hiphil",
    "hophal": "hophal",
    "hithpael": "hithpael",
    "polel": "polel",
    "palel": "palel",
    "pilel": "pilel",
    "poel": "poel",
    "pulal": "pulal",
    "polal": "polal",
    "pilpel": "pilpel",
    "polpal": "polpal",
    "hithpolel": "hithpolel",
    "hithpalpel": "hithpalpel",
    "pealal": "pealal",
    "poal": "poal",
    "nithpael": "nithpael",
}

# Maps Macula morph codes to our suffix IDs
morph_to_suffix = {
    "Sp1cs": "1cs",
    "Sp2ms": "2ms",
    "Sp2fs": "2fs",
    "Sp2mp": "2mp",
    "Sp2fp": "2fp",
    "Sp3ms": "3ms",
    "Sp3fs": "3fs",
    "Sp3mp": "3mp",
    "Sp3fp": "3fp",
    "So1cs": "1cs",  # object suffix (verb)
    "So2ms": "2ms",
    "So2fs": "2fs",
    "So3ms": "3ms",
    "So3fs": "3fs",
    "So1cp": "1cp",
    "So2mp": "2mp",
    "So2fp": "2fp",
    "So3mp": "3mp",
    "So3fp": "3fp",
}

# Prefix morph codes to prefix types
morph_to_prefix = {
    "Rd": "definite_article",
    "C": "conjunction",
    "R": "preposition",
}

# Preposition types
preposition_types = {"beth", "kaph", "lamed", "mem", "shin"}


@dataclass
class CellID:
    stem: str
    conjugation: str  # or noun type
    person: Optional[str]
    gender: Optional[str]
    number: Optional[str]
    state: Optional[str] = None
    is_noun: bool = False
    suffix: Optional[str] = None
    pronoun_object: Optional[str] = None
    proclitic: Optional[str] = None

    def to_string(self) -> str:
        parts = []

        if self.proclitic:
            parts.append(f"+{self.proclitic}")

        if self.is_noun:
            base = [self.conjugation, self.number or "", self.state or ""]
        else:
            base = [
                self.stem,
                self.conjugation,
                self.person or "",
                self.gender or "",
                self.number or "",
            ]

        result = ".".join(p for p in base if p)

        if self.pronoun_object:
            result += f"+{self.pronoun_object}"
        if self.suffix:
            result += f".{self.suffix}"

        return result

    def __str__(self) -> str:
        return self.to_string()


@dataclass
class Prefix:
    morph: str
    prefix_type: (
        str  # definite_article, conjunction, preposition, preposition_beth, etc.
    )
    surface: str
    description: str = ""

    def to_string(self) -> str:
        return f"+{self.prefix_type}:{self.surface}"


class ParadigmMapper:
    def __init__(self, paradigm_path: Optional[str] = None):
        path = Path(paradigm_path) if paradigm_path else PARADIGM_PATH
        with open(path, "r", encoding="utf-8") as f:
            self.paradigm = yaml.safe_load(f)
        self.stems = set(self.paradigm.get("stems", []))
        self.default_stems = set(default_stems.keys())

    def map_form(self, form: dict, lemma: str, stem: str) -> Optional[CellID]:
        form_type = form.get("type", "")

        if not form_type:
            return None

        if form_type in noun_types or not form_type:
            return self._map_noun(form, lemma)

        return self._map_verb(form, stem)

    def map_form_with_affixes(
        self, form: dict, lemma: str, stem: str
    ) -> tuple[Optional[CellID], List[Prefix]]:
        """Map a form to cell ID, also returning any prefixes."""
        cell = self.map_form(form, lemma, stem)
        prefixes = self._extract_prefixes(form)
        return cell, prefixes

    def _extract_prefixes(self, form: dict) -> List[Prefix]:
        """Extract prefixes from form data."""
        prefixes = []

        prefixes_data = form.get("prefixes", [])
        if prefixes_data:
            for p in prefixes_data:
                if p == "R":
                    prefixes.append(
                        Prefix(
                            morph="R",
                            prefix_type="definite_article",
                            surface="הְ",
                            description="definite article",
                        )
                    )
                elif p == "C":
                    prefixes.append(
                        Prefix(
                            morph="C",
                            prefix_type="conjunction",
                            surface="וְ",
                            description="conjunction vav",
                        )
                    )
                elif p in preposition_types:
                    prefixes.append(
                        Prefix(
                            morph="R",
                            prefix_type=f"preposition_{p}",
                            surface=f"{p}ְ",
                            description=f"preposition {p}",
                        )
                    )
                elif p == "S":
                    prefixes.append(
                        Prefix(
                            morph="S",
                            prefix_type="relative",
                            surface="שֶׁ",
                            description="relative particle",
                        )
                    )
                elif p == "T":
                    prefixes.append(
                        Prefix(
                            morph="T",
                            prefix_type="interrogative",
                            surface="הַ",
                            description="interrogative he",
                        )
                    )

        return prefixes

    def _map_verb(self, form: dict, stem: str) -> Optional[CellID]:
        form_type = form.get("type", "")

        conjugation = type_to_conjugation.get(form_type)
        if not conjugation:
            return None

        clean_stem = self._clean_stem(stem)

        person = form.get("person", "")
        gender = form.get("gender", "")
        number = form.get("number", "")

        if gender == "both":
            gender = "common"

        if conjugation in ("infinitive_construct", "infinitive_absolute"):
            person = ""
            gender = ""
            number = ""
        elif conjugation in ("participle_active", "participle_passive"):
            if person == "third":
                person = ""
        elif conjugation in ("jussive",):
            if not person:
                person = "third"

        suffix = self._map_suffix(form.get("pron_suffix_morph", ""))

        return CellID(
            stem=clean_stem or "qal",
            conjugation=conjugation,
            person=person if person else None,
            gender=gender if gender else None,
            number=number if number else None,
            is_noun=False,
            suffix=suffix,
        )

    def _map_noun(self, form: dict, lemma: str) -> Optional[CellID]:
        form_type = form.get("type", "common")
        if form_type not in noun_types:
            form_type = "common"

        gender = form.get("gender", "")
        if not gender or gender == "both":
            gender = "masculine"

        number = form.get("number", "singular")
        state = form.get("state", "absolute")

        if state not in ("absolute", "construct"):
            state = "absolute"

        if number not in ("singular", "plural", "dual"):
            number = "singular"

        n = {"singular": "s", "plural": "p", "dual": "d"}.get(number, "s")
        s = {"absolute": "a", "construct": "c"}.get(state, "a")

        suffix = self._map_suffix(form.get("pron_suffix_morph", ""))

        return CellID(
            stem="",
            conjugation=form_type,
            person=None,
            gender=gender if gender else None,
            number=n,
            state=s,
            is_noun=True,
            suffix=suffix,
        )

    def _map_suffix(self, morph: str) -> Optional[str]:
        """Map Macula morph code to our suffix ID."""
        if not morph:
            return None

        if morph in morph_to_suffix:
            return morph_to_suffix[morph]

        return None

    def _clean_stem(self, stem: str) -> str:
        if not stem:
            return "qal"

        if stem.startswith("unknown:"):
            return "qal"

        stem_lower = stem.lower()
        if stem_lower in default_stems:
            return default_stems[stem_lower]

        return stem_lower

    def validate_attestation(self, attestation_path: Optional[str] = None) -> dict:
        path = Path(attestation_path) if attestation_path else ATTESTATION_PATH

        with open(path, "r", encoding="utf-8") as f:
            attestation = json.load(f)

        results = {
            "total_forms": 0,
            "mapped": 0,
            "unmapped": 0,
            "unmapped_types": set(),
            "with_suffix": 0,
            "with_prefix": 0,
            "sample_mappings": [],
        }

        for lemma, stems in list(attestation.items())[:10]:
            for stem, forms in list(stems.items())[:3]:
                for form in forms[:2]:
                    results["total_forms"] += 1

                    cell = self.map_form(form, lemma, stem)
                    if cell:
                        results["mapped"] += 1

                        if cell.suffix:
                            results["with_suffix"] += 1

                        prefixes = form.get("prefixes", [])
                        if prefixes:
                            results["with_prefix"] += 1

                        if len(results["sample_mappings"]) < 20:
                            results["sample_mappings"].append(
                                {
                                    "lemma": lemma,
                                    "stem": stem,
                                    "type": form.get("type"),
                                    "surface": form.get("surface", ""),
                                    "cell_id": str(cell),
                                }
                            )
                    else:
                        results["unmapped"] += 1
                        results["unmapped_types"].add(form.get("type", ""))

        results["unmapped_types"] = sorted(results["unmapped_types"])

        return results


def main():
    mapper = ParadigmMapper()
    results = mapper.validate_attestation()

    print("=== Paradigm Validation Results ===")
    print(f"Total forms checked: {results['total_forms']}")
    print(f"Mapped: {results['mapped']}")
    print(f"With suffix: {results['with_suffix']}")
    print(f"With prefix: {results['with_prefix']}")
    print(f"Unmapped: {results['unmapped']}")
    print(f"Unmapped types: {results['unmapped_types']}")
    print()
    print("=== Sample Mappings ===")
    for m in results["sample_mappings"][:10]:
        print(f"  {m['surface']} ({m['type']}) -> {m['cell_id']}")


if __name__ == "__main__":
    main()
