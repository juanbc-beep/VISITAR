#!/usr/bin/env python3
"""Parse the Prestaciones Médicas <-> Nomenclador ÚNICO equivalence XLSX into a clean JSON."""
import json, sys
import openpyxl

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/unico_equivalencias.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/unico_equivalencias.json"

def fmt(c):
    if c is None:
        return None
    s = str(c).strip()
    return s.zfill(6) if len(s) < 6 else s

def clean(t):
    if not t:
        return ""
    return " ".join(str(t).split()).strip()

wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
ws = wb.active
rows = list(ws.iter_rows(min_row=2, values_only=True))

# best row per unico code (highest similarity)
best = {}
for r in rows:
    uni = fmt(r[2])
    if uni is None:
        continue
    try:
        score = float(r[8]) if r[8] is not None else 0.0
    except (TypeError, ValueError):
        score = 0.0
    rec = {
        "unico": uni,
        "unico_desc": clean(r[3]),
        "eq": fmt(r[0]),
        "eq_desc": clean(r[1]),
        "score": round(score, 4),
    }
    if uni not in best or score > best[uni]["score"]:
        best[uni] = rec

recs = list(best.values())
con = [r for r in recs if r["eq"]]
sin = [r for r in recs if not r["eq"]]
json.dump(recs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"unico codes: {len(recs)} | con equivalencia: {len(con)} | sin equivalencia: {len(sin)}", file=sys.stderr)
