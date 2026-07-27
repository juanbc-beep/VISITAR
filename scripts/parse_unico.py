#!/usr/bin/env python3
"""Parse the Prestaciones Médicas <-> Nomenclador ÚNICO equivalence XLSX into a clean JSON."""
import json, re, sys
import openpyxl

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/unico_equivalencias.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/unico_equivalencias.json"

# Ancho al que la planilla origen corta las descripciones.
SRC_CELL_CAP = 100

# Encabezados de observación / cobertura que en algunas filas vienen pegados al
# nombre de la práctica. Se separan a un campo propio; el texto queda literal.
OBS_PATTERNS = [
    re.compile(r"\s*(?=Observaci[oó]n(?:es)?\s*:)", re.I),
    re.compile(r"\s*(?=Se\s+asegura\s+la\s+cobertura)", re.I),
    re.compile(r"\s*(?=OBLIGACION\s+de\s+cobertura)", re.I),
]

def fmt(c):
    if c is None:
        return None
    s = str(c).strip()
    return s.zfill(6) if len(s) < 6 else s

def clean(t):
    if not t:
        return ""
    return " ".join(str(t).split()).strip()

RE_PAREN_FINAL = re.compile(r"\(([^)]*)\)\s*$")
RE_SOLO_MARCADOR = re.compile(r"^(?:NO\s+)?PMO\b(.*)$", re.I)
RE_SIGLAS = re.compile(r"(?:[A-Z]{1,3})(?:\s+[A-Z]{1,3})*")


def _es_marcador(inner):
    """¿El paréntesis final es sólo el marcador de clasificación?

    Sirve para "(NO PMO)", "(No PMO)", "(NO PMO SC)", "(NO PMO BF NC)". Se
    descarta a propósito el caso "(NO PMO pre CX Cataratas)", donde el paréntesis
    además aporta información clínica que debe quedar en el título.
    """
    m = RE_SOLO_MARCADOR.match(inner.strip())
    if not m:
        return False
    resto = m.group(1).strip()
    return (not resto) or bool(RE_SIGLAS.fullmatch(resto))


def split_desc(desc):
    """Separa (descripcion, observacion, marcador) cuando vienen en la misma celda."""
    marcador = None
    m = RE_PAREN_FINAL.search(desc)
    if m and _es_marcador(m.group(1)):
        marcador = clean(m.group(1))
        desc = desc[: m.start()].strip()
    corte = None
    for pat in OBS_PATTERNS:
        m = pat.search(desc)
        if m and (corte is None or m.start() < corte[0]):
            corte = (m.start(), m.end())
    if not corte:
        return desc.strip(" ·:;,-").strip(), None, marcador
    obs = desc[corte[1]:].strip(" ·:;,").strip()
    return desc[: corte[0]].strip(" ·:;,-").strip(), (obs or None), marcador

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
    desc_raw = clean(r[3])
    desc, obs, marcador = split_desc(desc_raw)
    rec = {
        "unico": uni,
        "unico_desc": desc or desc_raw,
        "eq": fmt(r[0]),
        "eq_desc": clean(r[1]),
        "score": round(score, 4),
    }
    if obs:
        rec["unico_obs"] = obs
    if marcador:
        rec["marcador"] = marcador
    if len(str(r[3] or "").rstrip()) >= SRC_CELL_CAP:
        rec["truncado"] = True
    if uni not in best or score > best[uni]["score"]:
        best[uni] = rec

recs = list(best.values())
con = [r for r in recs if r["eq"]]
sin = [r for r in recs if not r["eq"]]
json.dump(recs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"unico codes: {len(recs)} | con equivalencia: {len(con)} | sin equivalencia: {len(sin)}", file=sys.stderr)
