#!/usr/bin/env python3
"""Phase 7: Gap Generation & Lookup Table Export."""

import json
import csv
import unicodedata
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict

ATTESTATION_PATH = Path(__file__).parent.parent / "data" / "attestation.json"
GAPS_PATH = Path(__file__).parent.parent / "data" / "gaps.json"
OUTPUT_CSV = Path(__file__).parent.parent / "output" / "forms.csv"


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s) if s else s


PERFECT_SUFFIXES = {
    ("third", "masculine", "singular"): "",
    ("third", "feminine", "singular"): "",
    ("second", "masculine", "singular"): "תָ",
    ("second", "feminine", "singular"): "תָ",
    ("first", "common", "singular"): "תִ",
    ("third", "masculine", "plural"): "וּ",
    ("third", "feminine", "plural"): "וּ",
    ("second", "masculine", "plural"): "תֶּם",
    ("second", "feminine", "plural"): "תֶּן",
    ("first", "common", "plural"): "נוּ",
}


@dataclass
class FormEntry:
    surface: str = ""
    lemma: str = ""
    stem: str = ""
    cell_id: str = ""
    type: str = ""
    person: str = ""
    gender: str = ""
    number: str = ""
    state: str = ""
    pron_suffix: str = ""
    prefixes: str = ""
    attested: bool = True
    refs: List[str] = field(default_factory=list)


class GapGenerator:
    def __init__(self):
        self.attestation = self._load_attestation()
        self.entries: List[FormEntry] = []
        self._generate()

    def _load_attestation(self) -> dict:
        with open(ATTESTATION_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_gaps(self) -> dict:
        if GAPS_PATH.exists():
            with open(GAPS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _generate(self):
        gaps = self._load_gaps()
        gap_cells = self._parse_gaps(gaps)

        for lemma, stems in self.attestation.items():
            for stem, forms in stems.items():
                for form in forms:
                    entry = FormEntry(
                        surface=form.get("surface", ""),
                        lemma=lemma,
                        stem=stem if stem else "qal",
                        cell_id=self._make_cell_id(form, stem),
                        type=form.get("type", ""),
                        person=form.get("person", ""),
                        gender=form.get("gender", ""),
                        number=form.get("number", ""),
                        state=form.get("state", ""),
                        pron_suffix=form.get("pron_suffix_morph", ""),
                        prefixes=",".join(form.get("prefixes", [])),
                        attested=True,
                        refs=form.get("refs", []),
                    )
                    self.entries.append(entry)

        self._fill_gaps(gap_cells)

    def _parse_gaps(self, gaps: dict) -> Dict:
        result = defaultdict(lambda: defaultdict(set))
        for lemma, stem_data in gaps.items():
            for stem, missing_cells in stem_data.items():
                if not missing_cells:
                    continue
                for cell in missing_cells:
                    parts = cell.split(".")
                    if len(parts) >= 4:
                        result[nfc(lemma)][stem].add(cell)
        return result

    def _fill_gaps(self, gap_cells: dict):
        existing = set()
        for e in self.entries:
            key = (nfc(e.lemma), e.stem, e.type, e.person, e.gender, e.number)
            existing.add(key)

        for lemma_nfc, stems in gap_cells.items():
            for stem, missing in stems.items():
                for cell in missing:
                    parts = cell.split(".")
                    if len(parts) < 4:
                        continue
                    vtype, person, gender, number = (
                        parts[0],
                        parts[1],
                        parts[2],
                        parts[3],
                    )

                    key = (lemma_nfc, stem, vtype, person, gender, number)
                    if key in existing:
                        continue

                    if vtype != "qatal":
                        continue

                    suffix = PERFECT_SUFFIXES.get((person, gender, number), "")
                    base = lemma_nfc

                    if stem in ("hifil", "hiphil"):
                        if len(base) > 1:
                            base = "הִ" + base[1:]
                    elif stem in ("nifal",):
                        if len(base) > 1:
                            base = "נִ" + base[1:]
                    elif stem in ("hophal",):
                        if len(base) > 1:
                            base = "הָ" + base[1:]

                    generated = base + suffix

                    p = person[:3] if person else ""
                    g = gender[:3] if gender else ""
                    n = number[:3] if number else ""

                    entry = FormEntry(
                        surface=generated,
                        lemma=lemma_nfc,
                        stem=stem,
                        cell_id=f"{stem}.{vtype}.{p}{g}{n}",
                        type=vtype,
                        person=person,
                        gender=gender,
                        number=number,
                        state="",
                        pron_suffix="",
                        prefixes="",
                        attested=False,
                        refs=[],
                    )
                    self.entries.append(entry)

    def _make_cell_id(self, form: dict, stem: str) -> str:
        type_ = form.get("type", "")
        person = form.get("person", "")
        gender = form.get("gender", "")
        number = form.get("number", "")
        state = form.get("state", "")
        stem_clean = stem if stem else "qal"

        if type_ in ("common", "proper", "gentilic"):
            n = {"singular": "sg", "plural": "pl", "dual": "du"}.get(number, number)
            s = {"absolute": "abs", "construct": "cstr"}.get(state, state)
            return f"{type_}.{n}.{s}"
        else:
            p = person[:3] if person else ""
            g = gender[:3] if gender else ""
            n = number[:3] if number else ""
            return f"{stem_clean}.{type_}.{p}{g}{n}"

    def get_stats(self) -> Dict:
        stems = defaultdict(int)
        types = defaultdict(int)
        attested = 0
        generated = 0

        for entry in self.entries:
            stems[entry.stem] += 1
            types[entry.type] += 1
            if entry.attested:
                attested += 1
            else:
                generated += 1

        return {
            "total": len(self.entries),
            "attested": attested,
            "generated": generated,
            "by_stem": dict(stems),
            "by_type": dict(types),
        }

    def print_summary(self):
        stats = self.get_stats()
        print("=== Lookup Table Summary ===")
        print(
            f"Total: {stats['total']} (attested: {stats['attested']}, generated: {stats['generated']})"
        )
        print("\nBy Stem:")
        for stem, count in sorted(stats["by_stem"].items(), key=lambda x: -x[1]):
            print(f"  {stem}: {count}")

    def export_csv(self, path: Path = None) -> Path:
        output_path = path or OUTPUT_CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "surface",
            "lemma",
            "stem",
            "cell_id",
            "type",
            "person",
            "gender",
            "number",
            "state",
            "pron_suffix",
            "prefixes",
            "attested",
            "refs",
        ]

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for entry in self.entries:
                row = {
                    "surface": entry.surface,
                    "lemma": entry.lemma,
                    "stem": entry.stem,
                    "cell_id": entry.cell_id,
                    "type": entry.type,
                    "person": entry.person,
                    "gender": entry.gender,
                    "number": entry.number,
                    "state": entry.state,
                    "pron_suffix": entry.pron_suffix,
                    "prefixes": entry.prefixes,
                    "attested": "attested" if entry.attested else "generated",
                    "refs": "|".join(entry.refs[:5]) if entry.refs else "",
                }
                writer.writerow(row)

        print(f"Exported {len(self.entries)} forms to {output_path}")
        return output_path


def main():
    generator = GapGenerator()
    generator.print_summary()
    csv_path = generator.export_csv()
    print(f"\nCSV: {csv_path}")


if __name__ == "__main__":
    main()
