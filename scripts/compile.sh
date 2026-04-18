#!/bin/bash
# Compile Hebrew FST from LEXC files
# Usage: ./scripts/compile.sh

set -e
LEXICON="lexicon"
OUTPUT="build"

echo "=== Compiling Hebrew FST ==="

# Create build directory
mkdir -p "$OUTPUT"

# Step 1: Compile roots lexicon
echo "Compiling roots.lexc..."
foma -e "cd $LEXICON && read lexc roots.lexc" > "$OUTPUT/roots.fst" 2>&1 || true

# Step 2: Compile stems lexicon
echo "Compiling stems.lexc..."
foma -e "cd $LEXICON && read lexc stems.lexc" > "$OUTPUT/stems.fst" 2>&1 || true

# Step 3: Compile affixes
echo "Compiling affixes.lexc..."
foma -e "cd $LEXICON && read lexc affixes.lexc" > "$OUTPUT/affixes.fst" 2>&1 || true

# Step 4: Compile nouns
echo "Compiling nouns.lexc..."
foma -e "cd $LEXICON && read lexc nouns.lexc" > "$OUTPUT/nouns.fst" 2>&1 || true

echo "=== Done ==="
echo "FST files in $OUTPUT/"
ls -la "$OUTPUT/"