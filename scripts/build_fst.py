#!/usr/bin/env python3
"""
Build the Hebrew FST from LEXC sources using Foma.
Run: python scripts/build_fst.py
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LEXICON_DIR = PROJECT_ROOT / "lexicon"
PHONOLOGY_DIR = PROJECT_ROOT / "phonology"
BUILD_DIR = PROJECT_ROOT / "build"


def run_foma(commands: list) -> tuple:
    """Run foma with given commands."""
    cmd = ["foma", "-p", "-q"]
    result = subprocess.run(
        cmd,
        input="\n".join(commands),
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    return result.stdout, result.stderr, result.returncode


def compile_fst() -> Path | None:
    """Compile the full FST."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    print("Building Hebrew FST...")

    commands = [
        # Load all LEXC lexicons
        f"lexc {LEXICON_DIR / 'roots.lexc'}",
        f"lexc {LEXICON_DIR / 'stems.lexc'}",
        f"lexc {LEXICON_DIR / 'affixes.lexc'}",
        f"lexc {LEXICON_DIR / 'nouns.lexc'}",
        # Build the main FST by composing all components
        # This creates the full verb conjugation FST
        "define hebrew-fst Root",
        # Load phonology rules (these apply rewrite rules)
        f"xfst {PHONOLOGY_DIR / '01_weak_roots.xfst'}",
        f"xfst {PHONOLOGY_DIR / '02_dagesh.xfst'}",
        f"xfst {PHONOLOGY_DIR / '04_gutturals.xfst'}",
        f"xfst {PHONOLOGY_DIR / '05_vowels.xfst'}",
        f"xfst {PHONOLOGY_DIR / '06_final_forms.xfst'}",
        f"xfst {PHONOLOGY_DIR / '07_shewa.xfst'}",
        f"xfst {PHONOLOGY_DIR / '08_particles.xfst'}",
        # Combine (compose) phonology with lexicon
        "compose net",
        # Show stats
        "print size",
        # Save result
        f"save stack {BUILD_DIR / 'hebrew.fst'}",
        "quit",
    ]

    stdout, stderr, rc = run_foma(commands)
    print(stdout)
    if stderr:
        print(f"Warnings: {stderr}")

    if (BUILD_DIR / "hebrew.fst").exists():
        size = (BUILD_DIR / "hebrew.fst").stat().st_size
        print(f"\nFST built: {BUILD_DIR / 'hebrew.fst'} ({size:,} bytes)")
        return BUILD_DIR / "hebrew.fst"
    return None


def test_fst(fst_path: Path):
    """Test the FST."""
    print(f"\n=== Testing FST ===")

    # Test generation
    commands = [
        f"load {fst_path}",
        "apply down",
        "quit",
    ]

    test_cases = ["בָּרָא+qal+qatal+3ms"]
    for tc in test_cases:
        stdout, _, _ = run_foma(commands + [tc, ""])
        print(f"Input: {tc}")
        print(f"Output: {stdout.strip()}")


def main():
    fst_path = compile_fst()
    if fst_path:
        test_fst(fst_path)


if __name__ == "__main__":
    main()
