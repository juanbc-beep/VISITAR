#!/usr/bin/env python3
"""Relee las denominaciones del Catálogo de Prestaciones del PMO desde el PDF.

Por qué existe. El primer parser tomaba, para cada código, todo lo que caía en una
banda vertical alrededor de su renglón. Cuando arriba del código había un título de
sección —«Radiología», «Práctica»— el título se colaba adentro del nombre. Para
sacarlo se limpiaba después con una lista de palabras: si el nombre empezaba con
«Radiología», se le quitaba. Eso arregla «Radiología radioscopía simple» y rompe
«radiología del cráneo, cara, senos paranasales o cavum», donde esa palabra ES la
práctica. Resultado: 17 estudios del capítulo 34 quedaron con el nombre empezado
por la mitad —«del cráneo…», «articulación temporomandibular»— y buscar
«radiología» en Prestaciones Médicas no encontraba casi nada.

Cómo lo resuelve. No se limpia nada después: se lee bien de entrada. El nombre son
las palabras que están **a la derecha del código**, en su propio renglón y en los
renglones de continuación hasta el código siguiente. Un título de sección se
escribe a la misma altura que los códigos, en el margen izquierdo de la columna,
así que por construcción queda afuera y no hay nada que adivinar.

    python3 scripts/parse_pmo_titulos.py            # informe contra la base
    python3 scripts/parse_pmo_titulos.py --json x.json   # deja los títulos leídos
"""
import pdfplumber, re, json, sys, collections

PDF = "data/pmo.pdf"
COD = re.compile(r"^\d{6}$")
# Alto de renglón del PDF: los saltos normales son de 10 a 11 px. Más que esto ya
# es otro bloque de texto.
SALTO = 11.5


def _limpio(s):
    return re.sub(r"\s+", " ", s or "").strip(" :;-")


def leer(ruta=PDF):
    """code -> denominación tal como está impresa, sin títulos de sección."""
    pdf = pdfplumber.open(ruta)
    fuera = {}
    for pi, pg in enumerate(pdf.pages):
        ws = pg.extract_words(use_text_flow=False, keep_blank_chars=False)
        codes = [w for w in ws if COD.fullmatch(w["text"])]
        if not codes:
            continue
        # Las columnas se descubren solas: los códigos se alinean en dos x fijas.
        xs = collections.Counter(round(w["x0"]) for w in codes)
        cols = sorted(x for x, n in xs.items() if n >= 3)
        if not cols:
            continue
        for ci, cx in enumerate(cols):
            der = cols[ci + 1] - 6 if ci + 1 < len(cols) else 10 ** 6
            anclas = sorted([w for w in codes if abs(w["x0"] - cx) < 5], key=lambda w: w["top"])
            for i, a in enumerate(anclas):
                abajo = anclas[i + 1]["top"] - 2 if i + 1 < len(anclas) else 10 ** 6
                # A la derecha del código, en su renglón y en los de continuación.
                cand = [w for w in ws
                        if a["top"] - 2 <= w["top"] < abajo
                        and a["x1"] - 2 < w["x0"] < der
                        and not COD.fullmatch(w["text"])]
                # Los renglones de continuación van pegados, uno abajo del otro. Lo
                # que sigue después de un salto más grande ya no es la denominación:
                # es el texto del anexo de cobertura, que en esta página se imprime
                # en la misma columna. Sin esta regla, «fotocoagulación con yag
                # láser» se lleva puesto medio anexo.
                renglones = sorted(set(round(w["top"]) for w in cand))
                vale, ant = set(), None
                for t in renglones:
                    if ant is not None and t - ant > SALTO:
                        break
                    vale.add(t); ant = t
                nombre = sorted([w for w in cand if round(w["top"]) in vale],
                                key=lambda w: (round(w["top"]), w["x0"]))
                txt = _limpio(" ".join(w["text"] for w in nombre))
                # Palabras cortadas por el salto de renglón: «solici- tud».
                txt = re.sub(r"(\w)-\s+(\w)", r"\1\2", txt)
                if txt and (a["text"] not in fuera or len(txt) > len(fuera[a["text"]])):
                    fuera[a["text"]] = txt
    return fuera


def main():
    titulos = leer()
    print(f"códigos leídos del PDF: {len(titulos)}", file=sys.stderr)
    if "--json" in sys.argv:
        json.dump(titulos, open(sys.argv[sys.argv.index("--json") + 1], "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    try:
        cs = json.load(open("data/nbu_db.json", encoding="utf-8"))["codigos"]
    except FileNotFoundError:
        return
    faltan = []
    for c, t in sorted(titulos.items()):
        r = cs.get(c)
        if not r or r.get("nomenclador") != "PMO":
            continue
        act = _limpio(r["nombre"])
        if act.lower() != t.lower() and t.lower().endswith(act.lower()) and len(t) > len(act):
            faltan.append((c, t[:len(t) - len(act)].strip(), act))
    print(f"\nfichas del PMO a las que les falta el arranque: {len(faltan)}", file=sys.stderr)
    for c, ini, act in faltan:
        print(f"  {c}  «{ini}» + {act[:56]}", file=sys.stderr)


if __name__ == "__main__":
    main()
