#!/usr/bin/env python3
"""Simple CSV to SQLite export - debug version."""

import csv, os, sqlite3

# Delete old
try:
    os.unlink("output/forms.sqlite")
except:
    pass

conn = sqlite3.connect("output/forms.sqlite")
c = conn.cursor()

# Create manually
c.execute("""CREATE TABLE forms (
    surface TEXT,
    lemma TEXT,
    stem TEXT,
    cell_id TEXT,
    vtype TEXT,
    person TEXT,
    gender TEXT,
    number TEXT,
    state TEXT,
    pron_suffix TEXT,
    prefixes TEXT,
    attested TEXT,
    refs TEXT
)""")

# Count
count = 0
with open("output/forms.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        values = [row[k] for k in row.keys()]
        print(f"Row {count}: {len(values)} values - {values[:3]}...")
        if count > 2:
            break
        count += 1
