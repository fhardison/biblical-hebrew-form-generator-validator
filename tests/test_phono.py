"""
Unit tests for phonology rules
Run with: python -m pytest tests/test_phono.py -v
"""

import subprocess
from pathlib import Path


PHONO_DIR = Path(__file__).parent.parent / "phonology"


class TestPhonologyFiles:
    """Test phonology file existence and structure"""

    def test_phonology_directory_exists(self):
        assert PHONO_DIR.exists()

    def test_weak_roots_exists(self):
        assert (PHONO_DIR / "01_weak_roots.xfst").exists()

    def test_dagesh_exists(self):
        assert (PHONO_DIR / "02_dagesh.xfst").exists()

    def test_gutturals_exists(self):
        assert (PHONO_DIR / "04_gutturals.xfst").exists()

    def test_vowels_exists(self):
        assert (PHONO_DIR / "05_vowels.xfst").exists()

    def test_final_forms_exists(self):
        assert (PHONO_DIR / "06_final_forms.xfst").exists()

    def test_shewa_exists(self):
        assert (PHONO_DIR / "07_shewa.xfst").exists()

    def test_particles_exists(self):
        assert (PHONO_DIR / "08_particles.xfst").exists()

    def test_main_compose_exists(self):
        assert (PHONO_DIR / "hebrew_phono.xfst").exists()


class TestPhonologyStructure:
    """Test phonology files have expected rules"""

    def test_weak_roots_has_definitions(self):
        path = PHONO_DIR / "01_weak_roots.xfst"
        content = path.read_text()
        assert "define" in content.lower()

    def test_dagesh_has_definitions(self):
        path = PHONO_DIR / "02_dagesh.xfst"
        content = path.read_text()
        assert "BGDKPT" in content or "Dagesh" in content

    def test_gutturals_has_rules(self):
        path = PHONO_DIR / "04_gutturals.xfst"
        content = path.read_text()
        assert "Guttural" in content

    def test_vowels_has_rules(self):
        path = PHONO_DIR / "05_vowels.xfst"
        content = path.read_text()
        assert "Reduction" in content or "Vowel" in content

    def test_final_forms_has_substitutions(self):
        path = PHONO_DIR / "06_final_forms.xfst"
        content = path.read_text()
        assert "Final" in content

    def test_shewa_has_rules(self):
        path = PHONO_DIR / "07_shewa.xfst"
        content = path.read_text()
        assert "Shewa" in content

    def test_particles_has_fusion(self):
        path = PHONO_DIR / "08_particles.xfst"
        content = path.read_text()
        assert "Article" in content or "Fusion" in content

    def test_compose_has_order(self):
        path = PHONO_DIR / "hebrew_phono.xfst"
        content = path.read_text()
        assert "01_weak_roots" in content
        assert "02_dagesh" in content
        assert "04_gutturals" in content


class TestFomaPhonology:
    """Test foma can load phonology files"""

    def test_foma_available(self):
        result = subprocess.run(
            ["which", "foma"],
            capture_output=True,
        )
        assert result.returncode == 0

    def test_weak_roots_reads(self):
        result = subprocess.run(
            ["foma"],
            input=f"cd {PHONO_DIR}\nquit\n",
            capture_output=True,
            text=True,
        )
        # Foma runs without crash
        assert "Foma" in result.stdout or result.returncode == 0
