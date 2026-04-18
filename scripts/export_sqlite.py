#!/usr/bin/env python3
"""CSV to SQLite export with NFC normalization."""

import csv, sqlite3, os, unicodedata


def normalize(s):
    return unicodedata.normalize("NFC", s) if s else s


try:
    os.unlink("output/forms.sqlite")
except:
    pass

conn = sqlite3.connect("output/forms.sqlite")
c = conn.cursor()

cols = "surface,lemma,stem,cell_id,type,person,gender,number,state,pron_suffix,prefixes,attested,refs"
col_list = cols.split(",")
c.execute(f"CREATE TABLE forms ({','.join(c + ' TEXT' for c in col_list)})")

n = 0
with open("output/forms.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        vals = [normalize(r.get(c, "") or "") for c in col_list]
        c.execute(f"INSERT INTO forms VALUES ({','.join('?' * len(col_list))})", vals)
        n += 1

conn.commit()
c.execute("ALTER TABLE forms RENAME COLUMN type TO vtype")
conn.commit()
print(f"Done: {n} rows")
