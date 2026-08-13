#!/usr/bin/env python3
"""Vuelve a atar las equivalencias que quedaron colgando.

El Nomenclador Único trae, para cada práctica, el código equivalente del catálogo
del PMO. Cuando se armó la base, muchos de esos códigos **no existían todavía**
—capítulos enteros que faltaban: consultas, sanatoriales, neumonología,
hemodiálisis— así que la equivalencia quedó guardada con `destino_inexistente` y
sin `key`: la ficha del Único decía «el código equivalente no está cargado como
ficha propia todavía», y la del PMO no mostraba nada.

Ahora esos códigos sí existen. Este script recorre las equivalencias colgadas, y
donde el destino aparece:

  · del lado del ÚNICO   completa `key` y `desc`, y saca `destino_inexistente`.
  · del lado del PMO/NBU agrega el `equivalencia_unico` que faltaba, para que la
    ficha muestre el bloque «También en Nomenclador Único» con su U.B.

No inventa equivalencias: sólo usa las que la planilla del Único ya declaraba y
que apuntaban a un código que en ese momento no estaba.

    python3 scripts/reparar_equivalencias.py
    python3 scripts/inject_db.py
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "nbu_db.json")


def main():
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]
    atadas = ya = sin_destino = 0

    for k, v in cod.items():
        if v.get("nomenclador") != "UNICO":
            continue
        e = v.get("equivalencia")
        if not e or not e.get("destino_inexistente"):
            continue
        destino = e.get("code")
        if not destino or destino not in cod:
            sin_destino += 1
            continue

        r = cod[destino]
        # ── lado Único: la equivalencia pasa a ser navegable
        e["key"] = destino
        e["desc"] = r.get("nombre") or e.get("desc") or ""
        e.pop("destino_inexistente", None)
        atadas += 1

        # ── lado PMO/NBU: el bloque «También en Nomenclador Único»
        lista = r.setdefault("equivalencia_unico", [])
        if any(x.get("unico_key") == k for x in lista):
            ya += 1
            continue
        lista.append({
            "unico_code": v.get("code") or k.lstrip("U"),
            "unico_key": k,
            "unico_desc": v.get("nombre") or "",
            "score": e.get("score"),
            # «med» es el tipo que ya usan las equivalencias de prestaciones
            # médicas; «lab» queda para las del NBU.
            "tipo": "lab" if r.get("nomenclador") == "NBU" else "med",
        })

    json.dump(db, open(DB, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("equivalencias reatadas: %d" % atadas)
    print("  ya tenían el enlace de vuelta: %d" % ya)
    print("  siguen sin destino en la base: %d" % sin_destino)


if __name__ == "__main__":
    main()
