#!/usr/bin/env python3
"""Parse the laboratory part of the Nomenclador ÚNICO (VISITAR).
Único-lab code = 2 prefix digits + the 6-digit NBU code. Carries the U.B. value.

La celda de práctica de la planilla mezcla tres cosas distintas en un mismo texto:
el nombre de la práctica, un marcador de clasificación entre paréntesis —(PMO AA),
(NO PMO BF NC), etc.— y, en algunas filas, una observación o una obligación de
cobertura pegada al título. Acá se separan en campos propios; no se reescribe ni
se completa ningún texto: todo sale literal de la planilla.
"""
import json, re, sys
import xlrd

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/unico_lab.xls"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/unico_lab.json"

# Ancho al que la planilla origen corta las celdas: los textos de exactamente
# esta longitud vienen truncados y su final se perdió en la fuente.
SRC_CELL_CAP = 100

# Marcador de clasificación al final del título: "(PMO AA)", "(NO PMO  BF NC)"…
# La segunda variante cubre el marcador cortado por el truncado de la celda.
RE_MARCADOR = re.compile(r"\(\s*((?:NO\s+)?PMO\b[^)]*)\)\s*$", re.I)
RE_MARCADOR_CORTADO = re.compile(r"\(\s*(?:NO\s+)?PMO\b[^)]*$", re.I)

# Comienzos de observación pegados al título. Se prueban en orden y gana el que
# aparezca primero en el texto.
OBS_PATTERNS = [
    # "…Materia FecalObservaciones: …" / "UremiaObservaciones: …" (sin espacio)
    re.compile(r"\s*(?=Observaci[oó]n(?:es)?\s*:)", re.I),
    # "…PSA· OBLIGACION de cobertura en los siguientes casos: …"
    re.compile(r"\s*·\s*(?=OBLIGACION\s+de\s+cobertura)", re.I),
    re.compile(r"\s*(?=OBLIGACION\s+de\s+cobertura)", re.I),
    # "Hemograma: En éste código quedan incluidos …" / "Hepatograma completo: Este código incluye …"
    re.compile(r"\s*:\s*(?=(?:En\s+)?[eé]?ste\s+c[oó]digo\s+(?:quedan\s+)?inclu)", re.I),
    # "Epstein Barr anti vca IgM: iguales indicaciones que para el código 661055."
    re.compile(r"\s*:\s*(?=iguales\s+indicaciones)", re.I),
]


def codestr(v):
    if isinstance(v, float):
        return str(int(v))
    return str(v).strip()


def clean(t):
    return " ".join(str(t or "").split()).strip()


def split_practica(raw, truncado):
    """Separa la celda en (nombre, marcador, observacion).

    `truncado` se mide sobre la celda cruda —antes de colapsar espacios—, porque
    varias filas cortadas traen espacios dobles y al normalizarlas dejarían de
    alcanzar el tope y no se detectaría el corte.

    Todo lo devuelto es texto literal de la planilla: sólo se recorta y se
    reparte entre campos, nunca se completa lo que la fuente no trae.
    """
    texto = clean(raw)

    # 1) marcador de clasificación al final
    marcador = None
    m = RE_MARCADOR.search(texto)
    if m:
        marcador = clean(m.group(1))
        texto = texto[: m.start()].strip()
    elif truncado:
        # el truncado se comió el paréntesis de cierre: descartamos el jirón
        m2 = RE_MARCADOR_CORTADO.search(texto)
        if m2:
            texto = texto[: m2.start()].strip()

    # 2) observación pegada al título: corta en la primera coincidencia
    observacion = None
    corte = None
    for pat in OBS_PATTERNS:
        mm = pat.search(texto)
        if mm and (corte is None or mm.start() < corte[0]):
            corte = (mm.start(), mm.end())
    if corte:
        observacion = texto[corte[1]:].strip()
        texto = texto[: corte[0]].strip()

    # 3) prolijidad final: sin puntuación colgando de los cortes
    nombre = texto.strip(" ·:;,-").strip()
    if observacion:
        observacion = observacion.strip(" ·:;,").strip()
        observacion = re.sub(r"^Observaci[oó]n(?:es)?\s*:\s*", "", observacion, flags=re.I)
        observacion = observacion.strip() or None

    return nombre, marcador, observacion


wb = xlrd.open_workbook(SRC)
ws = wb.sheet_by_index(0)
out = []
seen = set()
n_marc = n_obs = n_trunc = 0
for r in range(1, ws.nrows):
    code = codestr(ws.cell_value(r, 0))
    celda = str(ws.cell_value(r, 1) or "")
    raw = clean(celda)
    ubv = ws.cell_value(r, 2)
    if len(code) != 8 or not raw:
        continue
    if code in seen:
        continue
    seen.add(code)
    try:
        ub = float(ubv)
    except (TypeError, ValueError):
        ub = None
    truncado = len(celda.rstrip()) >= SRC_CELL_CAP
    nombre, marcador, observacion = split_practica(raw, truncado)
    if not nombre:          # nunca dejar la ficha sin título
        nombre = raw
    rec = {"unico": code, "nombre": nombre, "nbu": code[-6:], "ub": ub}
    if marcador:
        rec["marcador"] = marcador
        n_marc += 1
    if observacion:
        rec["observacion"] = observacion
        n_obs += 1
    if truncado:
        rec["truncado"] = True
        n_trunc += 1
    out.append(rec)

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"unico-lab codes: {len(out)}", file=sys.stderr)
print(f"  títulos con marcador separado : {n_marc}", file=sys.stderr)
print(f"  títulos con observación separada: {n_obs}", file=sys.stderr)
print(f"  textos truncados en la fuente : {n_trunc}", file=sys.stderr)
