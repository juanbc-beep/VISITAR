#!/usr/bin/env python3
"""Parse the laboratory part of the Nomenclador ÚNICO (VISITAR).
Único-lab code = 2 prefix digits + the 6-digit NBU code. Carries the U.B. value."""
import json, re, sys
import xlrd

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/unico_lab.xls"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/unico_lab.json"

def codestr(v):
    if isinstance(v, float):
        return str(int(v))
    return str(v).strip()

def clean(t):
    return " ".join(str(t or "").split()).strip()

wb = xlrd.open_workbook(SRC)
ws = wb.sheet_by_index(0)
out = []
seen = set()
for r in range(1, ws.nrows):
    code = codestr(ws.cell_value(r, 0))
    name = clean(ws.cell_value(r, 1))
    ubv = ws.cell_value(r, 2)
    if len(code) != 8 or not name:
        continue
    if code in seen:
        continue
    seen.add(code)
    try:
        ub = float(ubv)
    except (TypeError, ValueError):
        ub = None
    out.append({"unico": code, "nombre": name, "nbu": code[-6:], "ub": ub})

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"unico-lab codes: {len(out)}", file=sys.stderr)
