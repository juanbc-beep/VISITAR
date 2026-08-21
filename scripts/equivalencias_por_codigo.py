#!/usr/bin/env python3
"""Corrige equivalencias UNICO→PMO cuando existe un código PMO idéntico.

Se originó en un caso puntual: el 290201 (PMO) «Polisomnografía con oximetría
en neonatos» aparecía sin equivalencia, mientras que el U290201 del Único —la
misma práctica, palabra por palabra— decía equivaler al PMO 290202 (una
práctica distinta, para adultos con CPAP). El match por proximidad de nombre
que arma `data/unico_equivalencias.xlsx` se corrió una fila: comparó cada
código del Único contra el PMO *siguiente* en vez del que comparte su propio
número, y encadenó el error en toda una serie (290201→290202→290203→…).

Regla: si un código del Único comparte número exacto con un código de
Prestaciones Médicas, y la equivalencia guardada apunta a otro código, se
corrige para que apunte al de número idéntico. Antes de escribir esto se
revisaron a mano los 40 casos que existían en la base (18/8/2026): en todos,
el nombre del código de número idéntico coincide con el del Único igual o
mejor que el destino que traía la planilla — incluidos los que a primera
vista parecían dudosos por tener nombres cortos del lado de Prestaciones
Médicas (p.ej. 121605 «cadera», que es la fila corta de la misma lista de
amputaciones que el Único describe completa).

⚠️ NO se aplica sin condiciones — dos casos ya demostraron que el número
puede coincidir por casualidad entre nomencladores que enumeran cosas
distintas (ver `equivalencias_renumeradas.py`, que dejó esto documentado a
mano): 430102 «cama individual con aislamiento» (Único) contra «una cama en
habitación de dos con baño» (PMO), y 420103 «consulta en consultorio C»
(Único, la letra C de su propia lista A/B/C/D…) contra «consulta médica en
horario nocturno y/o feriados» (PMO). Los dos ya estaban marcados
`sin_equivalencia: true` en la planilla original — este script respeta esa
marca y los deja como están, no la pisa.

El código NBU nunca coincide numéricamente con el Único (el Único prefija los
códigos de laboratorio con el bloque 60-64), así que esto sólo corrige contra
Prestaciones Médicas.

    python3 scripts/equivalencias_por_codigo.py
    python3 scripts/inject_db.py
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "nbu_db.json")


def main():
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]

    pmo_por_codigo = {v["code"]: (k, v) for k, v in cod.items() if v.get("nomenclador") == "PMO"}

    corregidas = 0
    for uk, v in cod.items():
        if v.get("nomenclador") != "UNICO":
            continue
        c = v.get("code")
        par = pmo_por_codigo.get(c)
        if not par:
            continue
        pk, p = par

        # Marca explícita de la planilla original: la coincidencia de número
        # es casualidad, no equivalencia. No se pisa.
        if v.get("sin_equivalencia"):
            continue

        e = v.get("equivalencia")
        if not e or e.get("code") == c:
            continue  # sin equivalencia guardada, o ya apunta al código idéntico

        # Sacar el reflejo viejo del código al que apuntaba mal, si lo tenía.
        viejo_key = e.get("key")
        if viejo_key and viejo_key != pk:
            viejo = cod.get(viejo_key)
            lista = viejo and viejo.get("equivalencia_unico")
            if lista:
                viejo["equivalencia_unico"] = [x for x in lista if x.get("unico_key") != uk]

        e.setdefault("code_declarado", e.get("code"))
        e.setdefault("desc_declarada", e.get("desc"))
        declarado = e["code_declarado"]

        e["code"] = c
        e["key"] = pk
        e["desc"] = p.get("nombre") or ""
        e["score"] = None
        e["recalculada"] = "codigo_corregido"
        e.pop("destino_inexistente", None)
        v["equivalencia"] = e

        nota = ("Equivalencia: la planilla del Nomenclador Único ataba este código al "
                "%s, pero existe el %s con número idéntico en Prestaciones Médicas. Se "
                "corrigió la equivalencia a ése." % (declarado, c))
        for rec in (v, p):
            aud = rec.setdefault("auditoria", [])
            if nota not in aud:
                aud.append(nota)

        lista = p.setdefault("equivalencia_unico", [])
        if not any(x.get("unico_key") == uk for x in lista):
            lista.append({
                "unico_code": c,
                "unico_key": uk,
                "unico_desc": v.get("nombre") or "",
                "score": None,
                "tipo": "med",
            })

        corregidas += 1
        print("  ✔ %s → %s  (apuntaba a %s)" % (uk, pk, declarado))

    json.dump(db, open(DB, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("equivalencias corregidas por código idéntico: %d" % corregidas)


if __name__ == "__main__":
    main()
