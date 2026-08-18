#!/usr/bin/env python3
"""Aplica la revisión manual de las equivalencias del Único que quedaron sin
destino resoluble (`equivalencia.destino_inexistente = true`).

De las 135 fichas del Único con la equivalencia colgando (el código que declara
la planilla no existe todavía como ficha propia — ver reparar_equivalencias.py),
el usuario revisó 134 contra la fuente y las separó en dos:

  · CORRECTAS: la equivalencia es real, sólo falta que se importe el capítulo o
    código de destino. No se tocan: siguen con `destino_inexistente` para que
    `reparar_equivalencias.py` las ate solas apenas ese código exista. Se deja
    constancia en la auditoría de que ya se revisaron a mano.
  · DESCARTADAS: el código que había declarado el emparejador automático no
    corresponde. Se saca la equivalencia (`equivalencia = null`,
    `sin_equivalencia = true`) para que la ficha diga «sin equivalencia
    hallada» en lugar de señalar a un código que no es.

La fuente es `data/equivalencias_sin_destino_revisadas.json`. No inventa nada:
sólo aplica lo que ese archivo ya declara.

    python3 scripts/descartar_equivalencias_invalidas.py
    python3 scripts/inject_db.py
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "nbu_db.json")
FUENTE = os.path.join(BASE, "data", "equivalencias_sin_destino_revisadas.json")


def main():
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]
    items = json.load(open(FUENTE, encoding="utf-8"))["items"]

    descartadas = verificadas = ya_resueltas = ausentes = discrepantes = 0

    for it in items:
        k = it["unico_key"]
        v = cod.get(k)
        if not v:
            ausentes += 1
            continue
        e = v.get("equivalencia")
        if not e or not e.get("destino_inexistente"):
            # Ya se ató sola (reparar_equivalencias.py corrió después de que se
            # importó el destino) o ya se descartó en una corrida anterior.
            ya_resueltas += 1
            continue
        if e.get("code") != it["codigo_declarado"]:
            # La planilla cambió de opinión desde que se armó la revisión: no
            # tocar sin volver a mirar.
            discrepantes += 1
            continue

        if it["veredicto"] == "descartado":
            v["equivalencia"] = None
            v["sin_equivalencia"] = True
            aud = v.setdefault("auditoria", [])
            nota = ("Revisado a mano (18/8/2026): el código declarado (%s %s) no "
                    "corresponde a esta práctica. Sin equivalencia." %
                    (it["nomenclador_destino"], it["codigo_declarado"]))
            if nota not in aud:
                aud.insert(0, nota)
            descartadas += 1
        else:
            aud = v.setdefault("auditoria", [])
            nota = ("Equivalencia declarada verificada a mano contra el nomenclador "
                    "impreso (18/8/2026): es correcta, pendiente de que se importe "
                    "el código de destino (%s %s)." %
                    (it["nomenclador_destino"], it["codigo_declarado"]))
            if nota not in aud:
                aud.append(nota)
            verificadas += 1

    json.dump(db, open(DB, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("descartadas (sin equivalencia ahora): %d" % descartadas)
    print("verificadas (siguen pendientes de importar el destino): %d" % verificadas)
    if ya_resueltas:
        print("ya resueltas o ya aplicadas antes: %d" % ya_resueltas)
    if ausentes:
        print("⚠ códigos del archivo que no están en la base: %d" % ausentes)
    if discrepantes:
        print("⚠ la equivalencia cambió desde la revisión, no se tocaron: %d" % discrepantes)


if __name__ == "__main__":
    main()
