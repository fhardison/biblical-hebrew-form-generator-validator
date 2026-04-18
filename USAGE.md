# Hebrew FST Usage Guide

## Quick Start

### Using the Python Wrapper

```python
from scripts.hebrew_fst import HebrewFST

# Create FST instance
fst = HebrewFST()

# Analyze a surface form
analyses = fst.analyze("בָּרָא")
for a in analyses:
    print(f"{a.surface} -> {a.lemma} [{a.stem}.{a.vtype}]")

fst.close()
```

### Using the SQLite Database

```python
import sqlite3
conn = sqlite3.connect('output/forms.sqlite')
```

### Understanding Gap-Filled Data

The lookup table contains both **attested** forms (from Macula) and **generated** forms (gap-filled):

```python
import sqlite3
conn = sqlite3.connect('output/forms.sqlite')

# Check if a form is attested or generated
cursor = conn.execute("""
    SELECT surface, lemma, stem, vtype, attested
    FROM forms
    WHERE lemma = 'בָּרָא' AND stem = 'piel'
""")
for row in cursor:
    print(f"{row[0]} [{row[1]} {row[2]}.{row[3]}] - {row[4]}")
# Output:
# בָּרָא [בָּרָא piel.qatal] - attested (for existing cells)
# בָּרָאתִ [בָּרָא piel.qatal] - generated (for missing cells)
```

**Key concept:** Gap-filling only generates forms for stems (binyanim) that are 
attested in the Macula corpus. If a lemma has ANY Piel form in Macula, missing Piel cells 
are generated. If a lemma has no Piel forms at all, no gap-filling occurs.

## Python Wrapper API

### HebrewFST Class

```python
from scripts.hebrew_fst import HebrewFST

# Initialize
fst = HebrewFST()

# Or with custom path
fst = HebrewFST("output/forms.sqlite")

# Context manager
with HebrewFST() as fst:
    # work with fst
    pass
```

### Methods

#### analyze(surface: str) -> List[Analysis]
Apply up: Analyze a surface form to get all possible morphological analyses.

```python
analyses = fst.analyze("בָּרָא")
for a in analyses:
    print(a.surface, a.lemma, a.stem, a.vtype, a.person, a.gender, a.number)
```

#### generate(lemma: str, stem: str, vtype: str, person: str, gender: str, number: str) -> List[str]
Apply down: Generate surface form(s) from lemma + features.

```python
# Generate all qatal forms
surfaces = fst.generate("בָּרָא", stem="qal", vtype="qatal")

# Generate specific form
surfaces = fst.generate("בָּרָא", stem="qal", vtype="qatal", 
                         person="third", gender="masculine", number="singular")
```

#### get_lemma_forms(lemma: str) -> List[Analysis]
Get all forms for a given lemma.

```python
forms = fst.get_lemma_forms("אֱלֹהִים")
```

#### get_stem_forms(stem: str) -> List[Analysis]
Get all forms for a given stem (binyan).

```python
forms = fst.get_stem_forms("qal")
```

#### validate(surface: str, lemma: str, stem: str = None) -> bool
Validate that a surface form is attested for a given lemma (optionally in a specific stem).

```python
# Check if בָּרָא is a valid Qal 3ms form
result = fst.validate("בָּרָא", "בָּרָא", "qal")
print(result)  # True

# Check if piel form exists
result = fst.validate("בָּרָא", "בָּרָא", "piel")  
print(result)  # True (if piel was attested in Macula)

# Check without specifying stem
result = fst.validate("בָּרָא", "בָּרָא")
print(result)  # True (any stem)
```

**Note:** Validation checks against the lookup table. If a stem was not attested for a lemma in Macula,
the form will not validate even if it could be morphologically valid.

#### search(pattern: str) -> List[Analysis]
Search surface forms matching a pattern (SQL LIKE).

```python
# Find all forms starting with בָּר
forms = fst.search("בָּר*")
```

#### get_conjugation_paradigm(lemma: str, stem: str) -> dict
Get full paradigm table for a verb.

```python
paradigm = fst.get_conjugation_paradigm("הָיָה", "qal")
# Returns: {"qatal": {"3ms": {"surface": "...", "cell_id": "..."}, ...}, ...}
```

### Analysis Dataclass

```python
from scripts.hebrew_fst import Analysis

a = Analysis(
    surface="בָּרָא",
    lemma="בָּרָא", 
    stem="qal",
    cell_id="qal.qatal.3ms",
    vtype="qatal",
    person="third",
    gender="masculine",
    number="singular",
    state="",
    pron_suffix="",
    refs=["GEN 1:1!2"]
)

print(a)  # בָּרָא -> בָּרָא [qal.qatal]
```

## Query Examples

### Find all forms of a lemma
```python
forms = fst.get_lemma_forms("אֱלֹהִים")
for f in forms:
    print(f.surface, f.vtype)
```

### Find all imperfect forms
```python
forms = fst.get_stem_forms("qal")
imperfect = [f for f in forms if f.vtype == "yiqtol"]
```

### Generate verb paradigm
```python
paradigm = fst.get_conjugation_paradigm("בָּרָא", "qal")
for vtype, cells in paradigm.items():
    print(f"{vtype}: {len(cells)} forms")
```

### Search patterns
```python
# Find nouns starting with מ
forms = fst.search("מ*")

# Find verbs with specific suffix
forms = fst.search("*וּ")
```

## CSV Format

| Column | Description |
|--------|-------------|
| surface | Vocalized surface form |
| lemma | Dictionary form |
| stem | Binyan (qal, niphal, piel, etc.) |
| cell_id | Paradigm cell identifier |
| vtype | Morphological type (qatal, yiqtol, common, etc.) |
| person | first/second/third |
| gender | masculine/feminine |
| number | singular/plural |
| state | absolute/construct |
| pron_suffix | Pronominal suffix code |
| prefixes | Prefix particles |
| attested | "attested" (from Macula) |
| refs | Bible references |

## Cell ID Format

Verb: `{stem}.{conjugation}.{person}{gender}{number}`
- Example: `qal.qatal.thirdmasculinesingular`

Noun: `{type}.{number}.{state}`
- Example: `common.sg.abs`

## Available Stems

```python
print(fst.stems)
# {'qal', 'niphal', 'piel', 'pual', 'hiphil', 'hophal', 'hithpael', ...}
```

## Available Types

```python
print(fst.vtypes)
# {'qatal', 'yiqtol', 'imperative', 'wayyiqtol', 'weqatal', 
#  'jussive', 'cohortative', 'infinitive construct', ...}
```

## Running Tests

```bash
python -m pytest tests/test_hebrew_fst.py -v
```