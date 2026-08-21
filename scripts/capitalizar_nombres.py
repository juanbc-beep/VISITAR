#!/usr/bin/env python3
"""Pone en mayúscula la primera letra de `nombre` en NBU/PMO/UNICO/ODO.

Hoy la mayúscula inicial depende de cómo venía cada fuente: algunas
planillas cargan el nombre tal cual lo escribe el nomenclador de origen
(mayúscula sostenida, o sólo la primera letra), otras —el Único, sobre
todo— lo traen entero en minúscula. El resultado es una lista donde una
ficha empieza con mayúscula y la de al lado no, sin ningún criterio.
Por regla ortográfica, un título arranca con mayúscula: se pone la
primera letra de `nombre` en mayúscula en las 2.136 fichas que hoy
empiezan en minúscula (PMO 1082 · Único 1050 · NBU 4 · Odontología 0).

⚠️ 4 nombres NO se tocan: son notación científica donde la minúscula
inicial es parte del término y ponerla en mayúscula sería un error, no una
corrección — «p53», «t-PA» y «pH» se escriben así en cualquier bibliografía.
Aparecen 7 veces entre NBU y Único (la misma práctica en los dos):

    667973 / U64667973   p53 Ac.
    667982 / U64667982   p53 mutante
    669597 / U64669597   t-PA INMUNOLÓGICO
    U60660741             pH

El resto de la palabra no se toca —sólo la primera letra—, así que esto no
altera abreviaturas ni siglas que ya estaban en mayúscula sostenida.

    python3 scripts/capitalizar_nombres.py
    python3 scripts/inject_db.py
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "nbu_db.json")

NOMENCLADORES = {"NBU", "PMO", "UNICO", "ODO"}

# Notación científica: la minúscula inicial es parte del término.
EXCEPCIONES = {
    "667973", "667982", "669597",           # NBU: p53 Ac. / p53 mutante / t-PA
    "U64667973", "U64667982", "U64669597",  # Único: los mismos, del lado del Único
    "U60660741",                            # Único: pH
}


def resincronizar_espejos(cod):
    """`equivalencia.desc` y `equivalencia_unico[].unico_desc` son una copia
    textual del `nombre` de otra ficha, tomada en el momento en que se armó
    la equivalencia (ver equivalencias_por_codigo.py y equivalencias_por_
    nombre.py). Si `nombre` cambia acá, esas copias quedan desactualizadas
    — la tarjeta de equivalencia mostraría la versión vieja mientras la
    ficha de destino ya muestra la nueva. Se recalculan contra el `nombre`
    actual. `desc_declarada` NO se toca: es a propósito una foto de cómo
    llamaba la planilla original a la práctica, no un espejo de `nombre`.
    """
    cambios = 0
    for v in cod.values():
        e = v.get("equivalencia")
        if e and e.get("key") and e["key"] in cod:
            nuevo = cod[e["key"]].get("nombre") or ""
            if e.get("desc") != nuevo:
                e["desc"] = nuevo
                cambios += 1
        for u in (v.get("equivalencia_unico") or []):
            if u.get("unico_key") and u["unico_key"] in cod:
                nuevo = cod[u["unico_key"]].get("nombre") or ""
                if u.get("unico_desc") != nuevo:
                    u["unico_desc"] = nuevo
                    cambios += 1
    return cambios


def main():
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]

    cambiadas = 0
    for k, v in cod.items():
        if v.get("nomenclador") not in NOMENCLADORES:
            continue
        if k in EXCEPCIONES:
            continue
        n = v.get("nombre")
        if not n or not n[0].isalpha() or not n[0].islower():
            continue
        v["nombre"] = n[0].upper() + n[1:]
        cambiadas += 1

    espejos = resincronizar_espejos(cod)

    json.dump(db, open(DB, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("nombres con mayúscula inicial corregida: %d" % cambiadas)
    print("copias de nombre resincronizadas (equivalencia.desc / unico_desc): %d" % espejos)


if __name__ == "__main__":
    main()
