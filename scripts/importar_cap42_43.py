#!/usr/bin/env python3
"""Suma a la base los capítulos 42 y 43 del Nomenclador Nacional con PMO.

Faltaban enteros. El 42 es CONSULTAS MÉDICAS —consultorio, domicilio, internación—
y no había ninguna en el manual: un administrativo que tenía que cargar una
consulta no la encontraba. El 43 son las prestaciones sanatoriales y de
enfermería, y de sus ~25 códigos había uno solo, «cama para acompañante».

Los datos salen de data/cap42_43_nn.json, transcripto a mano del PDF original
(páginas 145-150). El OCR de esas páginas es tan malo como el del capítulo 34, así
que se leyeron a ojo por el mismo motivo: acá hay aranceles y coseguros, y
adivinar un número no es una opción.

Se corre después de assemble.py, o suelto sobre data/nbu_db.json:

    python3 scripts/importar_cap42_43.py
    python3 scripts/inject_db.py
"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.path.join(BASE, "data", "cap42_43_nn.json")
DB = os.path.join(BASE, "data", "nbu_db.json")

SECCION = "PMO_MED"
SECCION_LABEL = "Catálogo PMO — prestaciones médicas"
NOM_FULL = ("Catálogo de Prestaciones del PMO — Programa Médico Obligatorio "
            "(Resolución 201/2002, S.S. Salud)")


def ficha(c, cap, titulo, normas_cap, normas_sueltas):
    """Arma una ficha con la misma forma que las que ya están en la base.

       El valor NO va como U.B.: estos capítulos se arancelan por «unidades» de
       honorarios y gastos, que es otra unidad. Meterlos como U.B. haría que la
       app los multiplicara por el valor de la Unidad Bioquímica y mostrara un
       arancel inventado.
    """
    aud = []
    if c.get("alcance"):
        aud.append("Alcance del Nomenclador Nacional: " + c["alcance"] + ".")
    if c.get("agregado_pmo"):
        aud.append("Código agregado por el P.M.O.")
    for n in normas_cap:
        aud.append(n)
    if c["code"] in normas_sueltas:
        aud.append("Norma del código: " + normas_sueltas[c["code"]])
    aud.append("Prestación incluida en el Catálogo de Prestaciones del PMO — "
               "cobertura obligatoria de los Agentes del Seguro de Salud (Res. 201/2002).")
    aud.append("Capítulo / especialidad: " + titulo + ".")

    partes = []
    if c.get("honorarios") is not None:
        partes.append("%s unidades de honorarios" % c["honorarios"])
    if c.get("total") is not None:
        partes.append("total práctica %s" % c["total"])
    if c.get("coseguro") is not None:
        partes.append("coseguro hasta %s" % c["coseguro"])
    arancel = ("Nomenclador Nacional: " + " · ".join(partes) + "."
               if partes else
               "Prestación del Catálogo del PMO (cobertura obligatoria). El arancel "
               "surge del nomenclador/convenio aplicable, no del NBU.")

    return {
        "code": c["code"],
        "nomenclador": "PMO",
        "nomenclador_full": NOM_FULL,
        "seccion": SECCION,
        "seccion_label": SECCION_LABEL,
        "grupo": c.get("grupo") or titulo,
        "nombre": c["nombre"],
        "sinonimos": [],
        "abreviaturas": [],
        # ub en None a propósito: ver el comentario de arriba.
        "valor": {"ub": None, "unidad": "—", "arancel": arancel},
        # requiere_norma en False a propósito: en la app ese flag se muestra como
        # «AUTORIZACIÓN: previa», y lo que estos capítulos traen son normas de
        # FACTURACIÓN —cuándo se factura el día de ingreso, qué incluye la cama—,
        # no un requisito de autorización. Las normas van en auditoría, que es
        # donde se leen como lo que son.
        "flags": {"urgencia": False, "requiere_norma": False,
                  "desuso": False, "pcr": False},
        "referencias": [],
        "norma": None,
        "frecuencia": [],
        "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
        "auditoria": aud,
        "alcance_nn": ({"texto": c["alcance"], "categoria": None, "fuente": "original"}
                       if c.get("alcance") else None),
        "en_catalogo_pmo": True,
    }


def main():
    src = json.load(open(FUENTE, encoding="utf-8"))
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]
    nuevos = pisados = 0
    for cap, d in src["capitulos"].items():
        normas = d.get("norma", [])
        sueltas = d.get("normas_sueltas", {})
        for c in d["codigos"]:
            f = ficha(c, cap, d["titulo"], normas, sueltas)
            if f["alcance_nn"] is None:
                f.pop("alcance_nn")
            if c["code"] in cod:
                # 430106 ya estaba: se respeta lo que había y sólo se completa.
                viejo = cod[c["code"]]
                for k, v in f.items():
                    if k not in viejo or not viejo[k]:
                        viejo[k] = v
                pisados += 1
            else:
                cod[c["code"]] = f
                nuevos += 1
    json.dump(db, open(DB, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("capítulos 42 y 43: %d fichas nuevas, %d completadas" % (nuevos, pisados))
    print("total de códigos en la base:", len(cod))


if __name__ == "__main__":
    main()
