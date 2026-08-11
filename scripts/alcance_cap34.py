#!/usr/bin/env python3
"""Qué abarca cada código del capítulo 34, y con qué código se cobra la exposición de más.

Regla del nomenclador, relevada por auditoría de VISITAR: **si la exposición tiene
código propio, ese código se carga aparte**; si las posiciones no tienen código
propio, son el alcance del código puntual. Ejemplo: una «Rx de tórax frente y
perfil» se carga con 340301 (la radiografía) **más** 340302 (la exposición
siguiente), porque 340302 existe como código independiente. En cambio 340204
—articulación temporomandibular— no tiene código de exposición siguiente: su
propio texto dice que abarca «tres posiciones, comparativas», y eso es alcance del
340204, no un código aparte.

El Nomenclador Nacional trae ese alcance impreso al lado de cada código, en la
misma línea que el PMO retiró («Texto retirado por el PMO»). Como el armado sale
del catálogo del PMO, ese renglón no llegaba nunca a la ficha: el agente veía «Rx
de tórax» sin saber que cubre una sola exposición.

El OCR de esas páginas está dañado, así que el texto se limpia de los errores
conocidos y **se muestra marcado como transcripción a confirmar**, con el original
guardado al lado. Nada de esto se inventa: sale de data/nn_values.json.
"""
import json, os, re, sys

# Errores del OCR que se repiten en estas páginas. Cada uno se vio en el texto.
ARREGLOS = [
    (r"subsigu?f?ente", "subsiguiente"), (r"exposici[oó]n?e?s?\b", None),
    (r"\bexposicion\b", "exposición"), (r"\bexposiciones\b", "exposiciones"),
    (r"\bprimeru\b", "primera"), (r"\bprimeraexposicion\b", "primera exposición"),
    (r"\bminimo\b", "mínimo"), (r"\buico\b", "único"), (r"\bunico\b", "único"),
    (r"\bplacus\b", "placas"), (r"\bpufmon\b", "pulmón"), (r"\besofogico\b", "esofágico"),
    (r"\bcardiacos\b", "cardíacos"), (r"\bestudlo\b", "estudio"), (r"\bEstomogo\b", "Estómago"),
    (r"\bocusalj?\b", "oclusal"), (r"\bfrentey\b", "frente y"), (r"\bcona sin\b", "con o sin"),
    (r"\bre lleno\b", "relleno"), (r"\bdeCOLON\b", "de colon"),
]
CAT = re.compile(r"[.\s]*([A-Z])[*#]?\s*$")          # la letra de categoría del Nacional
LEY = re.compile(r"T?e?x?t?[a-z]*\s*re[a-z]*\s*(?:por|pot|pore)?\s*e?l?\s*PM[OoD0]\s*[\]\|]?", re.I)
ENC = re.compile(r"P\.?M\.?O\.?\s*DE\s*PRACTICAS\s*ESPECIALIZADAS\s*CON\s*NOMENCLADOR\s*NACIONAL"
                 r"|APARATO\s*ESQUELETICO|APARATO\s*RESPIRATORIO|OBSERVA[CO]ONES\.?", re.I)


def _limpiar(t):
    t = re.sub(r"[（）]", lambda m: "(" if m.group() == "（" else ")", t)
    t = re.sub(r"(\w)- (\w)", r"\1\2", t)                 # palabras cortadas por el renglón
    for pat, rep in ARREGLOS:
        if rep:
            t = re.sub(pat, rep, t, flags=re.I)
    t = re.sub(r",(\S)", r", \1", t)                      # coma sin espacio
    t = re.sub(r"\)(\w)", r") \1", t)
    t = re.sub(r"(\w)\(", r"\1 (", t)
    return re.sub(r"\s+", " ", t).strip(" .,|]")


def alcances(records, log=None, base=""):
    for p in (os.path.join(base, "data/nn_values.json"), "nn_values.json"):
        try:
            nn = json.load(open(p, encoding="utf-8")); break
        except FileNotFoundError:
            nn = None
    if not nn:
        return 0
    n = par = 0
    for code in sorted(k for k in nn if k.startswith("34")):
        r = records.get(code)
        if not r or r.get("nomenclador") != "PMO":
            continue
        crudo = re.sub(r"\s+", " ", nn[code].get("nombre_ocr") or "")
        partes = LEY.split(ENC.sub(" ", crudo))
        if len(partes) < 2:
            continue
        txt = _limpiar(partes[-1])
        if not txt or len(txt) < 4:
            continue
        cat = None
        m = CAT.search(txt)
        if m:
            cat = m.group(1); txt = txt[:m.start()].strip(" .,")
        if not txt:
            continue
        r["alcance_nn"] = {"texto": txt[0].upper() + txt[1:], "categoria": cat,
                           "ocr": re.sub(r"\s+", " ", partes[-1]).strip(), "revisar": True}
        n += 1

    # Los pares: el código de la exposición siguiente es independiente y se carga
    # ADEMÁS del de la práctica. No es «está incluido en»: es un código más en la
    # misma solicitud, y esa es la diferencia entre facturar bien y facturar de
    # menos cuando el médico pide frente y perfil.
    for code, r in list(records.items()):
        sig = records.get(str(int(code) + 1)) if code.isdigit() and len(code) == 6 else None
        if not (r.get("nomenclador") == "PMO" and code.startswith("34") and sig):
            continue
        if "por exposición subsiguiente" not in (sig.get("nombre") or "").lower():
            continue
        r.setdefault("asoc_extra", None)
        aviso = ("Si el estudio lleva más de una exposición —por ejemplo frente y perfil—, "
                 "cada exposición adicional se carga aparte con el código " + sig["code"] +
                 ": es un código independiente, no está comprendido en éste.")
        if aviso not in r["auditoria"]:
            r["auditoria"].insert(0, aviso)
        avisos = ("Código independiente que se carga ADEMÁS del " + code + " — " +
                  (r["nombre"] or "") + " —, una vez por cada exposición que exceda la primera.")
        if avisos not in sig["auditoria"]:
            sig["auditoria"].insert(0, avisos)
        # «incluido_en» decía lo contrario de lo que pasa: no está comprendido.
        sig.get("relaciones", {})["incluido_en"] = []
        # Y en «cómo se carga», que es donde mira el que atiende.
        r["exposicion_siguiente"] = sig["code"]
        sig["exposicion_de"] = code
        par += 1
    if log:
        print(f"Capítulo 34: alcance leído del Nacional en {n} códigos · "
              f"pares práctica/exposición siguiente {par}", file=log)
    return n


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/nbu_db.json"
    db = json.load(open(ruta, encoding="utf-8"))
    alcances(db["codigos"], log=sys.stderr)
    json.dump(db, open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
    print("escrito " + ruta, file=sys.stderr)
