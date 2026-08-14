#!/usr/bin/env python3
"""Le pone a cada ficha ya cargada el «Texto retirado por el PMO» del Nacional.

El Nomenclador Nacional trae, al lado de cada práctica, un recuadro que el
Catálogo del PMO **no reproduce**: qué abarca el código, qué incluye, bajo qué
reglas se factura. Como el armado de la base sale del catálogo del PMO, ese
renglón no llegaba nunca a la ficha. El agente veía «fisioterapia» sin saber que
cubre horno de bier, onda corta, tracción cervical, iontoforesis y once cosas
más, todas por la misma sesión.

Esto es distinto de `importar_capitulos_nn.py`: aquél **crea** códigos de
capítulos que faltaban enteros. Éste no crea nada — le agrega la norma a códigos
que ya están.

⚠️ El PDF es un escaneo **sin capa de texto** (verificado: 0 caracteres en todas
las páginas), y el OCR de estas páginas viene destruido. Así que se lee a ojo y
se transcribe en `data/alcance_nn_pmo.json`. Para sumar un capítulo alcanza con
agregarlo ahí; el script no sabe ninguno de memoria.

⚠️ Se respeta la ortografía impresa. El original casi no acentúa y tiene erratas
propias («cógido» por «código», en el capítulo 25). No se corrigen: es el texto
normativo, y un auditor que compare contra el papel tiene que encontrar lo mismo.

Marca `fuente: "original"`, que es lo que hace que la ficha lo muestre sin el
cartel de «transcripción sin confirmar» —ese cartel es para lo que quedó del OCR
viejo, no para lo leído del PDF—.

Se corre después de assemble.py, o suelto sobre data/nbu_db.json:

    python3 scripts/alcance_nn_pmo.py
    python3 scripts/inject_db.py
"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.path.join(BASE, "data", "alcance_nn_pmo.json")
DB = os.path.join(BASE, "data", "nbu_db.json")

# El mismo prefijo que ya usan los importadores de capítulo, para que
# `normaNN()` en la app las reconozca sin cambiarle nada.
PREFIJO_NORMA = "Norma del código: "


def main():
    fuente = json.load(open(FUENTE, encoding="utf-8"))
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]
    nombres_antes = {k: v.get("nombre") for k, v in cod.items()}

    puestos = con_norma = faltantes = 0
    for cap, d in sorted(fuente["capitulos"].items()):
        normas = d.get("norma") or []
        codigos = d.get("codigos") or {}
        ausentes = [c for c in codigos if c not in cod]
        for c, texto in sorted(codigos.items()):
            r = cod.get(c)
            if not r:
                faltantes += 1
                continue
            if texto.strip():
                r["alcance_nn"] = {"texto": texto.strip(), "fuente": "original"}
                puestos += 1

        # La norma va en TODAS las fichas de su alcance, no sólo en las que
        # tienen texto propio: quien abre una sola ficha tiene que leer la regla
        # que la gobierna sin saber que existe un encabezado más arriba. Es el
        # mismo criterio que se usó con el material radioactivo del 26.
        #
        # `norma` gobierna el capítulo entero; `normas_prefijo` gobierna un
        # sub-capítulo. ⚠️ La distinción importa: el 12 tiene catorce normas de
        # sub-capítulo, y pegarle a los 146 códigos la del 12.01 —«el arancel
        # para el tratamiento no quirúrgico de las fracturas SIN DESPLAZAMIENTO
        # será el de la confección del yeso»— sería decirle al administrativo
        # que eso rige para las amputaciones.
        print("  cap %s · %-42s %2d texto(s), %d norma(s) de capítulo%s"
              % (cap, d.get("titulo", ""), len(codigos), len(normas),
                 "  ⚠ no están en la base: " + ", ".join(ausentes) if ausentes else ""))

        alcances = [(cap, normas)] + sorted((d.get("normas_prefijo") or {}).items())
        for pref, textos in alcances:
            if not textos:
                continue
            destino = [k for k, v in cod.items()
                       if v.get("nomenclador") == "PMO" and k.startswith(pref)]
            for k in destino:
                aud = cod[k].setdefault("auditoria", [])
                # primero, y sin repetir si se corre dos veces
                nuevas = [PREFIJO_NORMA + t for t in textos
                          if PREFIJO_NORMA + t not in aud]
                if nuevas:
                    cod[k]["auditoria"] = nuevas + aud
                    con_norma += 1
            if pref != cap:
                # ⚠️ Cero fichas no es un error del script: hay sub-capítulos que
                # el PMO vació entero, así que su norma no tiene dónde caer. Se
                # avisa para que quede a la vista y no pase por transcripción
                # perdida.
                print("     └ %s · %d norma(s) → %s"
                      % (pref, len(textos),
                         "%d ficha(s)" % len(destino) if destino
                         else "⚠ NINGUNA ficha con ese prefijo — norma sin destino"))

    movidos = [k for k, n in nombres_antes.items() if cod[k].get("nombre") != n]
    if movidos:
        sys.exit("✗ se modificaron nombres de ficha: %s" % movidos[:5])

    json.dump(db, open(DB, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("\ntextos puestos: %d · fichas que recibieron la norma del capítulo: %d"
          % (puestos, con_norma))
    if faltantes:
        print("códigos del JSON que no están en la base: %d" % faltantes)
    print("nombres de ficha intactos: %d verificados" % len(nombres_antes))


if __name__ == "__main__":
    main()
