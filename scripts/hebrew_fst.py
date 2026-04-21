#!/usr/bin/env python3
"""
Hebrew FST - Python wrapper for Biblical Hebrew morphological operations.
"""

import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class Analysis:
    """Represents a morphological analysis."""

    surface: str
    lemma: str
    stem: str
    cell_id: str
    vtype: str
    person: str
    gender: str
    number: str
    state: str
    pron_suffix: str
    refs: List[str] = None

    def __post_init__(self):
        if not self.refs:
            self.refs = []

    def __str__(self) -> str:
        return f"{self.surface} -> {self.lemma} [{self.stem}.{self.vtype}]"


class HebrewFST:
    """Biblical Hebrew FST wrapper."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or "output/forms.sqlite"
        self._conn = None
        self._stems = set()
        self._vtypes = set()
        self._load_schema()

    def _load_schema(self):
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self._conn = sqlite3.connect(self.db_path)

        self._stems = set(
            r[0]
            for r in self._conn.execute(
                "SELECT DISTINCT stem FROM forms WHERE stem != ''"
            ).fetchall()
        )

        self._vtypes = set(
            r[0]
            for r in self._conn.execute(
                "SELECT DISTINCT vtype FROM forms WHERE vtype != ''"
            ).fetchall()
        )

    @property
    def stems(self) -> Set[str]:
        return self._stems

    @property
    def vtypes(self) -> Set[str]:
        return self._vtypes

    def analyze(self, surface: str) -> List[Analysis]:
        """Analyze surface form."""
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)

        norm_surface = self._normalize(surface)

        # Try surface_norm column first (present in DBs built after the schema update)
        has_norm_col = any(
            row[1] == "surface_norm"
            for row in self._conn.execute("PRAGMA table_info(forms)").fetchall()
        )
        if has_norm_col:
            cursor = self._conn.execute(
                """
                SELECT surface, lemma, stem, cell_id, vtype, person, gender, number, state, pron_suffix, refs
                FROM forms WHERE surface_norm = ? LIMIT 100
                """,
                (norm_surface,),
            )
            return self._rows_to_analyses(cursor)

        # Fallback: direct match, then normalized match via consonant-filtered scan
        cursor = self._conn.execute(
            """
            SELECT surface, lemma, stem, cell_id, vtype, person, gender, number, state, pron_suffix, refs
            FROM forms WHERE surface = ? LIMIT 100
            """,
            (surface,),
        )
        rows = cursor.fetchall()

        if not rows:
            # DB may store cantillation marks; filter candidates by consonant pattern
            consonants = "".join(c for c in surface if 0x05D0 <= ord(c) <= 0x05EA)
            if consonants:
                pattern = "%" + "%".join(consonants) + "%"
                cursor = self._conn.execute(
                    """
                    SELECT surface, lemma, stem, cell_id, vtype, person, gender, number, state, pron_suffix, refs
                    FROM forms WHERE surface LIKE ? LIMIT 500
                    """,
                    (pattern,),
                )
                rows = [r for r in cursor.fetchall() if self._normalize(r[0]) == norm_surface]

        analyses = []
        for row in rows:
            refs = row[10].split("|") if row[10] else []
            analyses.append(
                Analysis(
                    surface=row[0],
                    lemma=row[1],
                    stem=row[2],
                    cell_id=row[3],
                    vtype=row[4],
                    person=row[5],
                    gender=row[6],
                    number=row[7],
                    state=row[8],
                    pron_suffix=row[9],
                    refs=refs,
                )
            )
        return analyses

    def generate(
        self,
        lemma: str,
        stem: str = "qal",
        vtype: str = "qatal",
        person: str = "",
        gender: str = "",
        number: str = "",
    ) -> List[str]:
        """Generate surface forms."""
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)

        params = [stem, vtype]
        query = "SELECT surface FROM forms WHERE stem = ? AND vtype = ?"

        if person and vtype not in ("common", "proper", "gentilic"):
            query += " AND person = ?"
            params.append(person)
        if gender and vtype not in ("common", "proper", "gentilic"):
            query += " AND gender = ?"
            params.append(gender)
        if number:
            query += " AND number = ?"
            params.append(number)

        results = set()
        cursor = self._conn.execute(query + " AND lemma = ?", params + [lemma])
        for row in cursor.fetchall():
            results.add(row[0])

        if not results:
            cursor = self._conn.execute(query, params)
            for row in cursor.fetchall():
                results.add(row[0])

        return list(results)[:50]

    def get_lemma_forms(self, lemma: str) -> List[Analysis]:
        """Get all forms for a lemma."""
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)

        cursor = self._conn.execute(
            """
            SELECT surface, lemma, stem, cell_id, vtype, person, gender, number, state, pron_suffix, refs
            FROM forms WHERE lemma LIKE ? OR lemma LIKE ? LIMIT 100
        """,
            (f"%{lemma}", lemma),
        )

        analyses = []
        for row in cursor.fetchall():
            refs = row[10].split("|") if row[10] else []
            analyses.append(
                Analysis(
                    surface=row[0],
                    lemma=row[1],
                    stem=row[2],
                    cell_id=row[3],
                    vtype=row[4],
                    person=row[5],
                    gender=row[6],
                    number=row[7],
                    state=row[8],
                    pron_suffix=row[9],
                    refs=refs,
                )
            )
        return analyses

    def get_stem_forms(self, stem: str) -> List[Analysis]:
        """Get all forms for a stem."""
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)

        cursor = self._conn.execute(
            """
            SELECT surface, lemma, stem, cell_id, vtype, person, gender, number, state, pron_suffix, refs
            FROM forms WHERE stem = ? LIMIT 100
        """,
            (stem,),
        )

        return self._rows_to_analyses(cursor)

    def search(self, pattern: str) -> List[Analysis]:
        """Search surface forms by pattern."""
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)

        sql_pattern = pattern.replace("*", "%").replace("?", "_")
        cursor = self._conn.execute(
            """
            SELECT surface, lemma, stem, cell_id, vtype, person, gender, number, state, pron_suffix, refs
            FROM forms WHERE surface LIKE ? LIMIT 50
        """,
            (sql_pattern,),
        )

        return self._rows_to_analyses(cursor)

    def get_conjugation_paradigm(self, lemma: str, stem: str = "qal") -> dict:
        """Get full paradigm for a verb."""
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)

        cursor = self._conn.execute(
            """
            SELECT vtype, person, gender, number, surface, cell_id
            FROM forms WHERE lemma LIKE ? AND stem = ?
            ORDER BY vtype, person, gender, number
        """,
            (f"%{lemma}", stem),
        )

        paradigm = {}
        for row in cursor.fetchall():
            vtype = row[0]
            if vtype not in paradigm:
                paradigm[vtype] = {}
            key = f"{row[1]}.{row[2]}.{row[3]}"
            paradigm[vtype][key] = {"surface": row[4], "cell_id": row[5]}

        return paradigm

    def _normalize(self, s: str) -> str:
        """Remove cantillation marks and normalize to NFC."""
        import unicodedata

        s = unicodedata.normalize("NFC", s)
        return "".join(c for c in s if not self._is_cantillation(c))

    def _is_cantillation(self, c: str) -> bool:
        """Check if character is a cantillation mark (0x0590-0x05AF, 0x05BD-0x05BF)."""
        code = ord(c)
        return (0x0590 <= code <= 0x05AF) or (0x05BD <= code <= 0x05BF)

    def validate(self, surface: str, lemma: str, stem: str = None) -> bool:
        """
        Validate that a surface form could be generated from a lemma.

        Args:
            surface: The surface form to validate (e.g., 'בָּרָא')
            lemma: The dictionary form (e.g., 'קטל')
            stem: Optional stem/binyan to restrict validation (e.g., 'qal', 'hifil')

        Returns:
            True if the surface form is attested for this lemma, False otherwise
        """
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)

        norm_surface = self._normalize(surface)
        norm_lemma = self._normalize(lemma)

        if stem:
            cursor = self._conn.execute(
                """
                SELECT surface, lemma FROM forms 
                WHERE lemma = ? AND stem = ?
            """,
                (norm_lemma, stem.lower()),
            )
        else:
            cursor = self._conn.execute(
                """
                SELECT surface, lemma FROM forms 
                WHERE lemma = ?
            """,
                (norm_lemma,),
            )

        for row_surface, row_lemma in cursor:
            if self._normalize(row_surface) == norm_surface:
                return True
        return False

    def _rows_to_analyses(self, cursor) -> List[Analysis]:
        analyses = []
        for row in cursor.fetchall():
            refs = row[10].split("|") if row[10] else []
            analyses.append(
                Analysis(
                    surface=row[0],
                    lemma=row[1],
                    stem=row[2],
                    cell_id=row[3],
                    vtype=row[4],
                    person=row[5],
                    gender=row[6],
                    number=row[7],
                    state=row[8],
                    pron_suffix=row[9],
                    refs=refs,
                )
            )
        return analyses

    def close(self):
        if self._conn:
            self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def main():
    print("=== Hebrew FST Demo ===")

    fst = HebrewFST()
    print(f"Stems: {len(fst.stems)} available")
    print(f"Types: {len(fst.vtypes)} available")

    # Analyze noun
    print("\n--- Analyze: אֱלֹהִים ---")
    for a in fst.analyze("אֱלֹהִים"):
        print(f"  {a}")

    # Generate verb
    print("\n--- Generate: qatal.3ms ---")
    for s in fst.generate("", "qal", "qatal", "third", "masculine", "singular")[:5]:
        print(f"  {s}")

    # Search
    print("\n--- Search: בָּר* ---")
    for a in fst.search("בָּר*")[:5]:
        print(f"  {a}")

    # Paradigm
    print("\n--- Paradigm: הָיָה (qal) ---")
    p = fst.get_conjugation_paradigm("הָיָה", "qal")
    for vtype, cells in p.items():
        print(f"  {vtype}: {len(cells)} forms")

    fst.close()


if __name__ == "__main__":
    main()
