#!/usr/bin/env python3
"""CSV to SQLite export with NFC normalization."""

import csv, sqlite3, os, unicodedata


def normalize(s):
    return unicodedata.normalize("NFC", s) if s else s


def normalize_surface(s):
    """NFC + strip cantillation marks for normalized lookup column."""
    if not s:
        return s
    s = unicodedata.normalize("NFC", s)
    return "".join(c for c in s if not (0x0590 <= ord(c) <= 0x05AF or 0x05BD <= ord(c) <= 0x05BF))


try:
    os.unlink("output/forms.sqlite")
except:
    pass

conn = sqlite3.connect("output/forms.sqlite")
c = conn.cursor()

cols = "surface,lemma,stem,cell_id,type,person,gender,number,state,pron_suffix,prefixes,attested,refs"
col_list = cols.split(",")
c.execute(f"CREATE TABLE forms ({','.join(col + ' TEXT' for col in col_list)}, surface_norm TEXT)")
c.execute("CREATE INDEX idx_surface_norm ON forms (surface_norm)")

n = 0
with open("output/forms.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        vals = [normalize(r.get(col, "") or "") for col in col_list]
        surface_norm = normalize_surface(vals[0])  # vals[0] is surface
        c.execute(f"INSERT INTO forms VALUES ({','.join('?' * (len(col_list) + 1))})", vals + [surface_norm])
        n += 1

conn.commit()
c.execute("ALTER TABLE forms RENAME COLUMN type TO vtype")
conn.commit()
print(f"Done: {n} rows")
