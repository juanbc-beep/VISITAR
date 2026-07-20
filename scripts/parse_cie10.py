#!/usr/bin/env python3
"""Parse the CIE-10 (ICD-10) PDF into category codes + descriptions, grouped by chapter."""
import json, re, sys
import pdfplumber

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/cie10.pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/cie10.json"

# CIE-10 chapters by code range (letter, low2, high2)
CAPS = [
    ("I",    "Ciertas enfermedades infecciosas y parasitarias", [("A",0,99),("B",0,99)]),
    ("II",   "Tumores (neoplasias)", [("C",0,99),("D",0,48)]),
    ("III",  "Enf. de la sangre y de los órganos hematopoyéticos", [("D",50,89)]),
    ("IV",   "Enf. endocrinas, nutricionales y metabólicas", [("E",0,90)]),
    ("V",    "Trastornos mentales y del comportamiento", [("F",0,99)]),
    ("VI",   "Enf. del sistema nervioso", [("G",0,99)]),
    ("VII",  "Enf. del ojo y sus anexos", [("H",0,59)]),
    ("VIII", "Enf. del oído y de la apófisis mastoides", [("H",60,95)]),
    ("IX",   "Enf. del sistema circulatorio", [("I",0,99)]),
    ("X",    "Enf. del sistema respiratorio", [("J",0,99)]),
    ("XI",   "Enf. del sistema digestivo", [("K",0,93)]),
    ("XII",  "Enf. de la piel y del tejido subcutáneo", [("L",0,99)]),
    ("XIII", "Enf. del sistema osteomuscular y tejido conjuntivo", [("M",0,99)]),
    ("XIV",  "Enf. del sistema genitourinario", [("N",0,99)]),
    ("XV",   "Embarazo, parto y puerperio", [("O",0,99)]),
    ("XVI",  "Afecciones originadas en el período perinatal", [("P",0,96)]),
    ("XVII", "Malformaciones congénitas y anomalías cromosómicas", [("Q",0,99)]),
    ("XVIII","Síntomas, signos y hallazgos anormales (clínicos y de laboratorio)", [("R",0,99)]),
    ("XIX",  "Traumatismos, envenenamientos y causas externas", [("S",0,99),("T",0,98)]),
    ("XX",   "Causas externas de morbilidad y mortalidad", [("V",1,99),("W",0,99),("X",0,99),("Y",0,98)]),
    ("XXI",  "Factores que influyen en el estado de salud (contacto con servicios)", [("Z",0,99)]),
    ("XXII", "Códigos para propósitos especiales", [("U",0,99)]),
]

def chapter(code):
    L = code[0]; n = int(code[1:])
    for rom, name, ranges in CAPS:
        for (l, lo, hi) in ranges:
            if l == L and lo <= n <= hi:
                return rom, name
    return "?", "Sin clasificar"

CODE_RE = re.compile(r"^([A-Z]\d{2})\s+(.+)$")

recs = {}
with pdfplumber.open(SRC) as pdf:
    for pg in pdf.pages:
        txt = pg.extract_text() or ""
        # join wrapped lines: a line not starting with a code is a continuation or a group header
        lines = txt.split("\n")
        i = 0
        while i < len(lines):
            ln = lines[i].strip()
            m = CODE_RE.match(ln)
            if m:
                code = m.group(1); desc = m.group(2).strip()
                # append continuation lines (next lines without a code and not a new group start)
                j = i + 1
                while j < len(lines):
                    nxt = lines[j].strip()
                    if not nxt or CODE_RE.match(nxt):
                        break
                    # continuation only if previous desc seems cut (heuristic: nxt is lowercase-ish continuation)
                    if nxt[0].islower() or nxt.startswith(("no clasific", "parte", "y ", "de ", "en ", "o ")):
                        desc += " " + nxt; j += 1
                    else:
                        break
                rom, cap = chapter(code)
                recs[code] = {"code": code, "desc": " ".join(desc.split()), "cap": rom, "cap_nombre": cap}
                i = j
            else:
                i += 1

caps_used = {}
for r in recs.values():
    caps_used[r["cap"]] = r["cap_nombre"]
json.dump({"codigos": recs, "capitulos": [{"rom": rom, "nombre": name} for rom, name, _ in CAPS if rom in caps_used]},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"CIE-10 categorías: {len(recs)}", file=sys.stderr)
from collections import Counter
print("por capítulo:", dict(Counter(r["cap"] for r in recs.values())), file=sys.stderr)
