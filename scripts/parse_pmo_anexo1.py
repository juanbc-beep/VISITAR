#!/usr/bin/env python3
"""Anexo I de la Res. 201/2002 (PMO) — estructura, no recortes.

Por qué existe este parser aparte:
el anterior barría el anexo con una expresión regular buscando oraciones que
tuvieran una cantidad y una palabra de límite. Eso devolvía frases sueltas sin
su marco de referencia: «10.14 Extracción de cuerpo extraño.» es un título de
práctica, no una regla, y «Hasta 30 días por año calendario.» no dice de qué.
Además exigía dos puntos para reconocer un apartado, así que los títulos salían
cortados a mitad de oración.

Acá se reconstruye el árbol tal como está en la norma: cada apartado numerado
(1., 1.1., 1.1.1., …) con su título y su texto completo, en orden de documento.
No se resume ni se reescribe nada: el texto es el de la fuente.

Salida: data/pmo_anexo1.json
  {"apartados":[{"num","nivel","titulo","texto","limites":[...]}]}
"""
import json, re, sys
import pdfplumber

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/pmo.pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/pmo_anexo1.json"

# ---------------------------------------------------------------- extracción
def col_lines(pg):
    """El PDF está a dos columnas: leerlo de corrido mezcla las dos."""
    mid = pg.width / 2
    words = pg.extract_words(use_text_flow=False)
    def lines(ws):
        ws = sorted(ws, key=lambda z: (round(z['top'] / 3), z['x0']))
        out, cur, ct = [], [], None
        for z in ws:
            if ct is None or abs(z['top'] - ct) < 4:
                cur.append(z['text'])
            else:
                out.append(' '.join(cur)); cur = [z['text']]
            ct = z['top']
        if cur: out.append(' '.join(cur))
        return out
    izq = [x for x in words if (x['x0'] + x['x1']) / 2 < mid]
    der = [x for x in words if (x['x0'] + x['x1']) / 2 >= mid]
    return lines(izq) + lines(der)

pdf = pdfplumber.open(SRC)
anexo, cur = {}, 0
for pi in range(len(pdf.pages)):
    t = pdf.pages[pi].extract_text() or ""
    for a, rom in [(1, 'I'), (2, 'II'), (3, 'III'), (4, 'IV')]:
        if re.search(r'ANEXO %s\b' % rom, t): cur = max(cur, a)
    anexo[pi] = cur

lineas = []
for pi in range(len(pdf.pages)):
    if anexo[pi] == 1:
        lineas += col_lines(pdf.pages[pi])

# ---------------------------------------------------------------- limpieza
# Encabezados y pies que se intercalan en medio de una oración. Sin sacarlos
# quedaban engendros como «no se cubrirán las leches 2 maternizadas».
BASURA = re.compile(
    r'^(ANEXO\s+[IVX]+|Actualizaci[óo]n\s+Normativa.*|S\.?S\.?SALUD.*|'
    r'P\.?M\.?O\.?E?\.?|\d{1,3})\s*$', re.I)

def limpiar(ls):
    return [l.strip() for l in ls if l.strip() and not BASURA.match(l.strip())]

lineas = limpiar(lineas)

# El anexo arranca después del encabezado de la resolución.
for i, l in enumerate(lineas):
    if l.startswith('Este Programa de Salud se refiere'):
        lineas = lineas[i:]; break

def unir(ls):
    """Rearma el párrafo deshaciendo el corte de palabras al final de renglón."""
    buf = ""
    for l in ls:
        if buf.endswith('-') and not buf.endswith(' -'):
            buf = buf[:-1] + l          # palabra partida: obligato- + rio
        elif buf:
            buf += ' ' + l
        else:
            buf = l
    return re.sub(r'\s+', ' ', buf).strip()

# ---------------------------------------------------------------- estructura
# Un apartado abre con su número al principio del renglón: «1.», «4.3.», «1.1.1.»
NUM = re.compile(r'^(\d+(?:\.\d+)*)\.\s+(\S.*)$')
# En la fuente hay títulos sin el punto detrás del número («4 Salud mental:»).
# Sin contemplarlo, ese capítulo entero se pegaba al final del anterior.
NUM2 = re.compile(r'^(\d{1,2})\s+([A-ZÁÉÍÓÚÑ][^.]{2,60}:)\s*$')
# El título es lo que va antes de los dos puntos o del primer punto seguido,
# siempre que sea corto: si no, no hay título y el apartado es todo texto.
TIT = re.compile(r'^([^:.]{3,70}):\s*(.*)$', re.S)

apartados = []
actual = None
preambulo = []

for l in lineas:
    m = NUM.match(l) or NUM2.match(l)
    if m:
        if actual: apartados.append(actual)
        actual = {"num": m.group(1), "cuerpo": [m.group(2)]}
    elif actual:
        actual["cuerpo"].append(l)
    else:
        preambulo.append(l)
if actual: apartados.append(actual)

# ---------------------------------------------------------------- armado
salida = []
for ap in apartados:
    texto = unir(ap["cuerpo"])
    if len(texto) < 4:
        continue
    titulo, resto = "", texto
    mt = TIT.match(texto)
    # Sólo se separa el título cuando lo que sigue arranca oración nueva. Si sigue
    # en minúscula es la misma frase («Programas de prevención de cánceres
    # femeninos: en especial de cáncer de mama…») y partirla dejaba el apartado
    # empezando a mitad de oración, que es justo lo que se quería evitar.
    if mt and len(mt.group(2)) > 20 and mt.group(2)[:1].isupper():
        titulo, resto = mt.group(1).strip(), mt.group(2).strip()
    elif len(texto) < 90 and not texto.endswith('.'):
        titulo, resto = texto.rstrip(':').strip(), ""
    salida.append({
        "num": ap["num"],
        "nivel": ap["num"].count('.') + 1,
        "titulo": titulo,
        "texto": resto,
    })

datos = {
    "fuente": "Resolución 201/2002 del Ministerio de Salud — Anexo I",
    "preambulo": unir(preambulo),
    "apartados": salida,
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=1)

niveles = {}
for a in salida: niveles[a["nivel"]] = niveles.get(a["nivel"], 0) + 1
print(f"Anexo I: {len(salida)} apartados {niveles} · "
      f"preámbulo {len(datos['preambulo'])} caracteres", file=sys.stderr)
