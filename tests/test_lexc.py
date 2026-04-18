"""
Unit tests for LEXC lexicon files
Run with: python -m pytest tests/test_lexc.py -v
"""

import subprocess
import tempfile
from pathlib import Path


LEXICON_DIR = Path(__file__).parent.parent / "lexicon"


class TestLexcCompilation:
    """Test that all LEXC files compile in foma"""

    def test_roots_lexc_loads(self):
        result = subprocess.run(
            ["foma"],
            input=f"cd {LEXICON_DIR}\nread lexc roots.lexc\nquit\n",
            capture_output=True,
            text=True,
        )
        # Warnings are OK, *Error is not
        assert "*Error" not in result.stdout

    def test_stems_lexc_loads(self):
        result = subprocess.run(
            ["foma"],
            input=f"cd {LEXICON_DIR}\nread lexc stems.lexc\nquit\n",
            capture_output=True,
            text=True,
        )
        assert "*Error" not in result.stdout

    def test_affixes_lexc_loads(self):
        result = subprocess.run(
            ["foma"],
            input=f"cd {LEXICON_DIR}\nread lexc affixes.lexc\nquit\n",
            capture_output=True,
            text=True,
        )
        assert "*Error" not in result.stdout

    def test_nouns_lexc_loads(self):
        result = subprocess.run(
            ["foma"],
            input=f"cd {LEXICON_DIR}\nread lexc nouns.lexc\nquit\n",
            capture_output=True,
            text=True,
        )
        assert "*Error" not in result.stdout


class TestLexiconStructure:
    """Test that lexicons have required components"""

    def test_roots_has_continuation_class(self):
        path = LEXICON_DIR / "roots.lexc"
        content = path.read_text()
        assert "LEXICON Root" in content or "LEXICON roots" in content.lower()

    def test_stems_has_all_binyanim(self):
        path = LEXICON_DIR / "stems.lexc"
        content = path.read_text()
        assert "LEXICON qal" in content
        assert "LEXICON niphal" in content
        assert "LEXICON piel" in content
        assert "LEXICON pual" in content
        assert "LEXICON hiphil" in content
        assert "LEXICON hophal" in content
        assert "LEXICON hithpael" in content

    def test_affixes_has_suffixes(self):
        path = LEXICON_DIR / "affixes.lexc"
        content = path.read_text()
        assert "SUF-PERF" in content or "PERF" in content
        assert "OBJ-SUF" in content or "POS-SUF" in content

    def test_nouns_has_declensions(self):
        path = LEXICON_DIR / "nouns.lexc"
        content = path.read_text()
        assert "QATAL-M" in content or "SEGHOLATE" in content
        assert "FEM-AH" in content or "FEM-T" in content


class TestLexiconFiles:
    """Test file existence"""

    def test_lexicon_directory_exists(self):
        assert LEXICON_DIR.exists()

    def test_roots_lexc_exists(self):
        assert (LEXICON_DIR / "roots.lexc").exists()

    def test_stems_lexc_exists(self):
        assert (LEXICON_DIR / "stems.lexc").exists()

    def test_affixes_lexc_exists(self):
        assert (LEXICON_DIR / "affixes.lexc").exists()

    def test_nouns_lexc_exists(self):
        assert (LEXICON_DIR / "nouns.lexc").exists()

    def test_master_paradigm_exists(self):
        assert (LEXICON_DIR / "master_paradigm.yaml").exists()


class TestFomaAvailable:
    """Test foma is available"""

    def test_foma_command_exists(self):
        result = subprocess.run(
            ["which", "foma"],
            capture_output=True,
        )
        assert result.returncode == 0

    def test_foma_runs(self):
        result = subprocess.run(
            ["foma", "-v"],
            capture_output=True,
            text=True,
        )
        assert "Foma" in result.stdout or result.returncode == 0
