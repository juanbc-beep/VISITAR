#!/usr/bin/env python3
"""Lleva el «Qué abarca este código» (alcance_nn) a la ficha equivalente del Único.

El pedido del usuario: lo que dice un código del Nomenclador de Prestaciones
Médicas o del NBU sobre qué abarca —el recuadro «Texto retirado por el PMO»,
transcripto por alcance_nn_pmo.py— tiene que verse también desde el código
equivalente del Único, porque son la misma práctica con otro número. Hoy la
ficha del Único no repite ese texto: quien entra por ahí no se entera de qué
abarca la prestación que está cargando.

No es lo mismo que `propagar_al_unico.py`: aquél sólo ata el laboratorio
(Único ↔ NBU) y no toca `alcance_nn`. Éste cubre las dos puntas —Único médico
↔ PMO y Único laboratorio ↔ NBU— y sólo este campo.

Sólo copia cuando la equivalencia está resuelta (`key` presente, no
`destino_inexistente`): si el destino todavía no existe en la base no hay de
dónde copiar. `fuente` queda en `"original"` porque el texto sigue siendo el
mismo renglón transcripto del PDF — lo que cambia es a qué código de la base
se le muestra, no su origen. Queda una línea en la auditoría de qué código lo
trae, para que quien lo lea sepa que no es el Único quien lo dice.

    python3 scripts/propagar_abarca_unico.py
    python3 scripts/inject_db.py
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "nbu_db.json")


def main():
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]
    nombres_antes = {k: v.get("nombre") for k, v in cod.items()}

    nuevos = actualizados = sin_fuente = 0
    for k, v in cod.items():
        if v.get("nomenclador") != "UNICO":
            continue
        e = v.get("equivalencia")
        if not e or not e.get("key") or e.get("destino_inexistente"):
            continue
        origen = cod.get(e["key"])
        if not origen:
            continue
        fuente = origen.get("alcance_nn")
        if not fuente or not fuente.get("texto"):
            sin_fuente += 1
            continue

        antes = v.get("alcance_nn")
        if antes and antes.get("texto") == fuente["texto"]:
            continue  # ya estaba, no repetir la línea de auditoría

        v["alcance_nn"] = {"texto": fuente["texto"], "fuente": fuente.get("fuente", "original")}
        nota = "Abarca heredado de la equivalencia en %s (%s)." % (
            e.get("target_label") or e.get("target_nom") or "el otro nomenclador", origen["code"])
        aud = v.setdefault("auditoria", [])
        if nota not in aud:
            aud.insert(0, nota)
        if antes:
            actualizados += 1
        else:
            nuevos += 1

    movidos = [k for k, n in nombres_antes.items() if cod[k].get("nombre") != n]
    if movidos:
        raise SystemExit("✗ se modificaron nombres de ficha: %s" % movidos[:5])

    json.dump(db, open(DB, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("abarca heredado — nuevo: %d · actualizado: %d · sin texto para heredar: %d"
          % (nuevos, actualizados, sin_fuente))


if __name__ == "__main__":
    main()
