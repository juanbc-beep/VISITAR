#!/usr/bin/env python3
"""Las cinco equivalencias donde el Único declara un número que no existe.

Hay un puñado de prácticas en las que la planilla del Nomenclador Único dice
«equivale al código NNNNNN» y ese número no está en el Nomenclador Nacional —
pero la práctica sí está, **con el mismo número que usa el Único**. Es decir: el
destino declarado viene de otra numeración, y la equivalencia real es el propio
número.

    Único 280201 «lavado alveolar»  →  dice 280208 (no existe)
                                    →  el Nacional lo tiene como 280201

No se hace por regla automática «si el número coincide, atalo»: en el capítulo 43
el número 430102 coincide y la práctica es OTRA —el Único dice «cama en
habitación individual (aislamiento)» y el Nacional dice «una cama en habitación
de dos con baño»—. Atarlas por coincidencia de número habría metido un error de
facturación. Por eso la lista de abajo está escrita a mano, código por código,
mirando el nombre de los dos lados, y aprobada por el usuario.

El número que declaraba la planilla no se tira: queda en `code_declarado` y en
una línea de auditoría, porque un auditor que compare contra el papel se va a
encontrar con ese número y tiene que poder explicárselo.

    python3 scripts/equivalencias_renumeradas.py
    python3 scripts/inject_db.py
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "nbu_db.json")

# (clave del Único, código real del Nacional). Verificadas de a una: mismo
# número y misma práctica de los dos lados.
PARES = [
    ("U280111", "280111"),   # capacidad pulmonar total y volumen residual
    ("U280201", "280201"),   # lavado alveolar
    ("U280301", "280301"),   # ablación de lesiones broncopulmonares por endoscopía
    ("U260528", "260528"),   # perfusión sanguínea miocárdica con radioisótopos
    ("U430601", "430601"),   # luminoterapia
]

# ⚠️ NO entra: U430102 → 430102. El número coincide pero la práctica no
# (individual con aislamiento vs. habitación de dos). Queda sin equivalencia.


def main():
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]
    hechas = 0

    for uk, destino in PARES:
        v = cod.get(uk)
        if not v:
            print("  ⚠ falta en la base: %s" % uk)
            continue
        r = cod.get(destino)
        if not r:
            print("  ⚠ el destino no existe: %s" % destino)
            continue
        e = v.get("equivalencia") or {}
        declarado = e.get("code")

        e["code_declarado"] = declarado
        e["code"] = destino
        e["key"] = destino
        e["desc"] = r.get("nombre") or e.get("desc") or ""
        e["renumerado"] = True
        e.pop("destino_inexistente", None)
        v["equivalencia"] = e

        nota = ("Equivalencia: la planilla del Nomenclador Único declara el código "
                "%s, que no existe en el Nomenclador Nacional. La práctica está en el "
                "Nacional con el mismo número que usa el Único (%s) y con el mismo "
                "nombre, así que la equivalencia se ató a ése." % (declarado, destino))
        for c in (v, r):
            aud = c.setdefault("auditoria", [])
            if nota not in aud:
                aud.append(nota)

        lista = r.setdefault("equivalencia_unico", [])
        if not any(x.get("unico_key") == uk for x in lista):
            lista.append({
                "unico_code": v.get("code") or uk.lstrip("U"),
                "unico_key": uk,
                "unico_desc": v.get("nombre") or "",
                "score": e.get("score"),
                "tipo": "lab" if r.get("nomenclador") == "NBU" else "med",
            })
        hechas += 1
        print("  ✔ %s → %s  (la planilla decía %s)" % (uk, destino, declarado))

    json.dump(db, open(DB, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("equivalencias renumeradas: %d de %d" % (hechas, len(PARES)))


if __name__ == "__main__":
    main()
