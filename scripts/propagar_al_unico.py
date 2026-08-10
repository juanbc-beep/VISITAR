#!/usr/bin/env python3
"""Hace que la ficha del Único muestre todo lo que muestra su equivalente del NBU.

El laboratorio del Nomenclador Único es el NBU con otro número de código: cada
práctica está dos veces en la base, una con el código del NBU (660192) y otra
con el del Único (60660192). Si son la misma práctica, el agente que la busca
por un lado tiene que ver lo mismo que si la busca por el otro; que dependa de
por dónde entró es lo que hace que se cargue mal.

El armado ya copiaba norma, relaciones, flags, frecuencia y auditoría. Faltaba
todo lo que se calcula DESPUÉS de ese momento (tipo de muestra, abreviaturas
sugeridas) y todo lo que sale del nombre del NBU, que el Único no tiene porque
su planilla trae el nombre abreviado: sinónimos, siglas, sección de origen.

Se corre solo desde assemble.py al final del armado, y a mano sobre una base ya
armada:

    python3 scripts/propagar_al_unico.py data/nbu_db.json

Dos reglas que no se cruzan:

1. La valorización NO se toca. El Único trae su propia U.B. de la planilla de
   VISITAR y en 101 prácticas no coincide con la del NBU. Esa diferencia es
   deliberada: es el convenio, no un error de carga. Se agrega la U.B. del NBU
   como referencia, en un campo aparte y rotulado como tal.

2. El tipo de muestra NO se pisa. En 13 pares el nombre del Único y el del NBU
   dicen muestras distintas (669990: el NBU dice zinc urinario y el Único, zinc
   en semen). Pisar uno con el otro dejaría una ficha que se contradice sola.
   Se hereda sólo cuando el Único no tiene nada, y cuando se contradicen queda
   escrito en la auditoría para que alguien revise la equivalencia.
"""
import json, sys

# Lo que la ficha del Único no puede sacar de su propia planilla y sí está en el
# NBU. Se copia sólo si del lado del Único no hay nada: nunca pisa un dato cargado.
HEREDA_SI_FALTA = [
    "sinonimos",        # alimentan la búsqueda: sin esto el Único no aparece al buscar por sinónimo
    "abreviaturas",     # ídem, y se ven como chips en la ficha
    "referencias",
    "en_catalogo_pmo",  # el cartel «También en Catálogo PMO»
    "cie_rel", "leyes_rel",
    "cobertura_pmo", "cobertura_tipo", "tope_pmo",
    "surge", "seriado", "frecuencia", "lateralidad", "lateralidad_origen",
]

# Acá el NBU manda: es la fuente normativa y el Único es una copia suya.
PISA_SIEMPRE = ["norma", "flags"]


def _vacio(v):
    return v is None or v == [] or v == {} or v == "" or v is False


def propagar(records, log=None):
    """Aplica la propagación sobre el diccionario de fichas. Devuelve el resumen."""
    pares = []
    for k, c in records.items():
        if c.get("nomenclador") != "UNICO":
            continue
        eq = c.get("equivalencia") or {}
        if eq.get("target_nom") == "NBU" and eq.get("key") in records:
            pares.append((k, eq["key"]))

    # Para traducir el par sangre/orina a los códigos del Único.
    gemelo = {n: u for u, n in pares}
    st = {"pares": len(pares), "campos": 0, "norma": 0, "muestra": 0,
          "par_muestra": 0, "abrev": 0, "seccion": 0, "valor_ref": 0, "chocan": 0}

    for uk, nk in pares:
        U, N = records[uk], records[nk]

        for f in HEREDA_SI_FALTA:
            if not _vacio(N.get(f)) and _vacio(U.get(f)):
                U[f] = json.loads(json.dumps(N[f]))
                st["campos"] += 1

        for f in PISA_SIEMPRE:
            if not _vacio(N.get(f)):
                antes = json.dumps(U.get(f), sort_keys=True, ensure_ascii=False)
                U[f] = json.loads(json.dumps(N[f]))
                if antes != json.dumps(U[f], sort_keys=True, ensure_ascii=False):
                    st["norma"] += 1

        # De qué parte del NBU viene. Es lo que distingue una práctica especial
        # (P.E.) de una del PMO, y en la ficha del Único no se veía por ningún
        # lado: su sección propia dice «Único — Laboratorio · <grupo>».
        if N.get("seccion_label") and U.get("nbu_seccion_label") != N["seccion_label"]:
            U["nbu_seccion"] = N.get("seccion")
            U["nbu_seccion_label"] = N["seccion_label"]
            st["seccion"] += 1

        # La U.B. del NBU, como referencia y sin tocar la del Único.
        v = N.get("valor") or {}
        ref = {k: v[k] for k in ("ub", "ub_vigente", "ub_actualizado_2024") if v.get(k) is not None}
        if ref:
            U["nbu_valor"] = ref
            st["valor_ref"] += 1

        # Tipo de muestra: heredar sólo el hueco, marcar la contradicción.
        if N.get("muestra"):
            if not U.get("muestra"):
                U["muestra"] = list(N["muestra"])
                U["muestra_origen"] = "equivalencia"
                st["muestra"] += 1
            elif not (set(U["muestra"]) & set(N["muestra"])):
                # Sólo cuando no comparten ninguna muestra. Que una diga «orina» y
                # la otra «sérico o urinario» no es una contradicción: es que el
                # nombre del Único viene más corto. Contradicción es que una diga
                # orina y la otra sangre, y nada en común.
                aviso = ("Revisar la equivalencia: el nombre del Único indica " +
                         " y ".join(U["muestra"]) + " y el del NBU " + N["code"] + ", " +
                         " y ".join(N["muestra"]) + ".")
                if aviso not in U.get("auditoria", []):
                    U.setdefault("auditoria", []).append(aviso)
                st["chocan"] += 1

        # El par sangre/orina, con el código del Único cuando el gemelo existe.
        if N.get("par_muestra") and not U.get("par_muestra"):
            p = dict(N["par_muestra"])
            g = gemelo.get(p.get("key"))
            if g:
                p = {"key": g, "code": records[g]["code"], "nombre": records[g]["nombre"],
                     "muestra": p["muestra"]}
            U["par_muestra"] = p
            st["par_muestra"] += 1

        # Siglas con las que el médico puede escribir la práctica en la orden:
        # las dos listas salen de nombres distintos, así que se suman.
        a = list(U.get("abrev_posibles") or [])
        for x in (N.get("abrev_posibles") or []):
            if x not in a:
                a.append(x)
        if a and a != (U.get("abrev_posibles") or []):
            U["abrev_posibles"] = a[:6]
            st["abrev"] += 1

    if log:
        print(f"Único ← NBU: pares {st['pares']} · campos heredados {st['campos']} · "
              f"norma/flags reescritos {st['norma']} · muestra heredada {st['muestra']} "
              f"(en conflicto {st['chocan']}) · par sangre/orina {st['par_muestra']} · "
              f"siglas {st['abrev']} · sección de origen {st['seccion']} · "
              f"U.B. de referencia {st['valor_ref']}", file=log)
    return st


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/nbu_db.json"
    db = json.load(open(ruta, encoding="utf-8"))
    propagar(db["codigos"], log=sys.stderr)
    # Sin indentado, que es como está guardada la base en el repositorio: así el
    # cambio que se ve en git son las fichas tocadas y no el archivo entero.
    json.dump(db, open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
    print("escrito " + ruta, file=sys.stderr)
