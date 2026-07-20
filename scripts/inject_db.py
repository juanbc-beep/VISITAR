#!/usr/bin/env python3
"""Embed data/nbu_db.json into web/index.html as gzip+base64 (single-file, offline, ~75% smaller)."""
import re, gzip, base64, sys

HTML = "web/index.html"
DB = "data/nbu_db.json"

raw = open(DB, "rb").read()
gz = gzip.compress(raw, 9)
b64 = base64.b64encode(gz).decode("ascii")

html = open(HTML, encoding="utf-8").read()
block = f'<script id="nbu-db-gz" type="text/plain">{b64}</script>'
# match either the legacy JSON block or an existing gz block
pat = re.compile(r'<script id="nbu-db(?:-gz)?"[^>]*>.*?</script>', re.S)
new, n = pat.subn(block, html, count=1)
if n != 1:
    print("ERROR: no DB script block found", file=sys.stderr); sys.exit(1)
open(HTML, "w", encoding="utf-8").write(new)
print(f"JSON {len(raw)/1e6:.2f} MB -> gzip {len(gz)/1e6:.2f} MB -> base64 {len(b64)/1e6:.2f} MB · HTML {len(new)/1e6:.2f} MB")
