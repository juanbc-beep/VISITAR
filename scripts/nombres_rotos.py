#!/usr/bin/env python3
"""Devuelve su nombre a las fichas donde el OCR viejo metió la etiqueta del recuadro.

El Nomenclador Nacional marca lo que el P.M.O. sacó con un recuadro que dice
«Texto retirado por el PMO». En los renglones donde ese texto arranca la línea
—porque el P.M.O. retiró el título entero de la práctica— el OCR con el que se
armó la base se comió la etiqueta **como si fuera parte del nombre**:

    080210  «TextotetradoporelPMO»          ← el nombre es SÓLO la basura
    121931  «Texto retfirado porel PMO Pasta de Unna»
    120202  «PMOEsternon,escapufa,humero,(excepto supracondilea) cubito yfo radio…»

⚠️ Esto NO contradice la regla de no tocar nombres. Esa regla existe para que se
respete la redacción de cada nomenclador; lo que hay guardado acá no es la
redacción de ninguno, es una transcripción rota que incluye una sigla que no
pertenece al nombre de ninguna práctica. `080210` es el caso extremo: un
administrativo que busca «laparoscopía» no encuentra la ficha, porque la palabra
no está en ninguna parte.

**Cómo se detectan**: buscando `pmo` en el nombre normalizado sin espacios ni
acentos. Es señal suficiente —esa sigla no aparece en el nombre de ninguna
práctica— y encuentra también los casos donde la etiqueta quedó pegada a la
palabra siguiente, que un patrón con espacios se pierde.

⚠️ **El nombre viejo no se tira**: queda en la auditoría de la ficha. Quien
compare contra una exportación anterior tiene que poder explicar la diferencia.

    python3 scripts/nombres_rotos.py
    python3 scripts/inject_db.py
"""
import json, os, re, unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.path.join(BASE, "data", "nombres_rotos.json")
DB = os.path.join(BASE, "data", "nbu_db.json")


def plano(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)


def rotos(cod):
    """Los que todavía tienen la etiqueta metida en el nombre."""
    return sorted(k for k, v in cod.items()
                  if v.get("nomenclador") == "PMO" and "pmo" in plano(v.get("nombre")))


def main():
    fuente = json.load(open(FUENTE, encoding="utf-8"))["nombres"]
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]

    antes = rotos(cod)
    arreglados = 0
    for c, d in sorted(fuente.items()):
        r = cod.get(c)
        if not r:
            print("  ⚠ %s no está en la base" % c)
            continue
        viejo = r.get("nombre") or ""
        nuevo = d["nombre"]
        if viejo == nuevo:
            continue
        nota = ("Nombre corregido contra el PDF del Nomenclador Nacional (página %s del "
                "archivo). El OCR con el que se armó la base había metido la etiqueta "
                "«Texto retirado por el PMO» dentro del nombre. Decía: «%s»."
                % (d.get("pag", "?"), viejo))
        aud = r.setdefault("auditoria", [])
        if nota not in aud:
            aud.append(nota)
        r["nombre"] = nuevo
        arreglados += 1
        print("  ✔ %s  «%s»\n        ← «%s»" % (c, nuevo[:74], viejo[:74]))

    json.dump(db, open(DB, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

    quedan = rotos(cod)
    print("\nnombres corregidos: %d" % arreglados)
    print("estaban rotos: %d · quedan rotos: %d" % (len(antes), len(quedan)))
    if quedan:
        print("todavía sin corregir (falta leer su página del PDF):")
        for k in quedan:
            print("   %s  %s" % (k, (cod[k].get("nombre") or "")[:76]))


if __name__ == "__main__":
    main()
