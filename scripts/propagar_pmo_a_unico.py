#!/usr/bin/env python3
"""Hace que la ficha del Único (médico) muestre toda la información adicional
que tiene su equivalente de Prestaciones Médicas (PMO/Nomenclador Nacional).

Mismo problema que resuelve `propagar_al_unico.py` para el laboratorio, del
lado médico: cada práctica está dos veces en la base —una con el código del
PMO y otra con el del Único—, y si son la misma práctica el agente que la
busca por un lado tiene que ver lo mismo que si la busca por el otro.

⚠️ El NOMBRE del Único NO se toca nunca, a propósito: es el nomenclador que
usa la empresa, y su redacción es la que vale para el equipo, aunque a veces
difiera de cómo lo dice la planilla de Prestaciones Médicas. Lo que faltaba
del lado del Único no era el nombre — era la información ADICIONAL que sólo
se había cargado del lado de Prestaciones Médicas durante los barridos de
"galenos sin cargar" y las 159 denominaciones (28/8/2026): el valor real de
honorarios de galeno, la obligación de cobertura del PMO, el coseguro.

Reglas:

1. Los campos de HEREDA_SI_FALTA se copian sólo cuando el Único no tiene
   nada propio — nunca pisan un dato ya cargado del lado del Único.
2. `valores`/`asociaciones_especificas` (honorarios de galeno) se heredan
   igual, porque son números de una fuente única —el Nomenclador Nacional—,
   no una valorización propia del Único: su propio campo `valor.arancel` ya
   dice literalmente "sin valorización cargada" cuando no tiene nada.
3. El coseguro es un monto, no está en ningún lado visible salvo metido en
   la prosa de `valor.arancel` del PMO — se agrega la misma frase al arancel
   del Único, dejando explícito que es heredado (mismo criterio que usa
   `propagar_abarca_unico.py` para "Abarca heredado de...").
4. Se corre a mano sobre una base ya armada. Ver si conviene sumarlo a
   assemble.py junto a `propagar_al_unico.py` (éste cubre NBU↔Único; ahí
   falta el mismo mecanismo para PMO↔Único):

    python3 scripts/propagar_pmo_a_unico.py
    python3 scripts/inject_db.py
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "nbu_db.json")

# Información adicional que el Único puede no tener por venir de su propia
# planilla (que no trae estos datos). Se copia sólo si del lado del Único no
# hay nada: nunca pisa lo que ya esté cargado ahí.
HEREDA_SI_FALTA = [
    "cobertura_pmo", "cobertura_tipo", "tope_pmo",
    "en_catalogo_pmo", "aviso_nomenclador",
    "referencias", "sinonimos", "abreviaturas",
    "surge", "seriado", "frecuencia",
]


def _vacio(v):
    return v is None or v == [] or v == {} or v == "" or v is False


def propagar(records, log=None):
    pares = []
    for k, c in records.items():
        if c.get("nomenclador") != "UNICO":
            continue
        eq = c.get("equivalencia") or {}
        if eq.get("target_nom") == "PMO" and eq.get("key") in records:
            pares.append((k, eq["key"]))

    st = {"pares": len(pares), "campos": 0, "valores": 0, "coseguro": 0}
    nombres_antes = {k: v.get("nombre") for k, v in records.items()}

    for uk, pk in pares:
        U, P = records[uk], records[pk]

        for f in HEREDA_SI_FALTA:
            if not _vacio(P.get(f)) and _vacio(U.get(f)):
                U[f] = json.loads(json.dumps(P[f]))
                st["campos"] += 1

        # Honorarios reales de galeno: mismos números, misma fuente (el
        # Nomenclador Nacional) — el Único no tiene una valorización propia
        # con la que puedan entrar en conflicto (ver punto 2 del docstring).
        if not _vacio(P.get("valores")) and _vacio(U.get("valores")):
            U["valores"] = json.loads(json.dumps(P["valores"]))
            if not _vacio(P.get("asociaciones_especificas")):
                U["asociaciones_especificas"] = list(P["asociaciones_especificas"])
            nota = "Valorización heredada de la equivalencia en Prestaciones Médicas (%s)." % P["code"]
            aud = U.setdefault("auditoria", [])
            if nota not in aud:
                aud.insert(0, nota)
            st["valores"] += 1

        # Coseguro: sólo vive como monto (`coseguro_hasta`) y metido en la
        # prosa de `valor.arancel` del lado PMO — no hay dónde más mostrarlo
        # hoy, así que se agrega la misma frase al arancel del Único.
        cos = P.get("coseguro_hasta")
        if cos and not U.get("coseguro_hasta"):
            U["coseguro_hasta"] = cos
            arancel = (U.get("valor") or {}).get("arancel") or ""
            frase = " Coseguro hasta $%s (heredado de la equivalencia en Prestaciones Médicas, %s)." % (
                ("%g" % cos), P["code"])
            if "Coseguro hasta" not in arancel:
                U.setdefault("valor", {})["arancel"] = arancel.rstrip() + frase
            st["coseguro"] += 1

    movidos = [k for k, n in nombres_antes.items() if records[k].get("nombre") != n]
    if movidos:
        raise SystemExit("✗ se modificaron nombres de ficha: %s" % movidos[:5])

    if log:
        print(f"PMO → Único: pares {st['pares']} · campos heredados {st['campos']} · "
              f"valorización heredada {st['valores']} · coseguro heredado {st['coseguro']}", file=log)
    return st


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else DB
    db = json.load(open(ruta, encoding="utf-8"))
    propagar(db["codigos"], log=sys.stderr)
    json.dump(db, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("escrito " + ruta, file=sys.stderr)
