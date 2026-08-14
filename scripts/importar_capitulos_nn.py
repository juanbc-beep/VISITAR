#!/usr/bin/env python3
"""Suma a la base los capítulos del Nomenclador Nacional que faltaban.

Hoy son el 40, 41, 42, 43 y 44. Faltaban enteros:

  40/41  Terapia intensiva e internación por 24 horas.
  42     CONSULTAS MÉDICAS —consultorio, domicilio, internación—. No había
         ninguna en el manual: un administrativo que tenía que cargar una
         consulta médica no la encontraba.
  43     Prestaciones sanatoriales y de enfermería. De ~25 códigos había uno.
  44     Unidad coronaria móvil. ⚠️ El original lo marca «Capítulo del Nom.Nac.
         retirado por el PMO»: existe en el Nacional pero está fuera del catálogo
         obligatorio, y eso queda escrito en la ficha.

Los datos salen de data/capitulos_nn.json, transcripto a mano del PDF original
(páginas 145-150). El OCR de esas páginas es tan malo como el del capítulo 34, así
que se leyeron a ojo por el mismo motivo: acá hay aranceles y coseguros, y
adivinar un número no es una opción.

Para sumar otro capítulo alcanza con agregarlo al JSON; el script no lo sabe de
memoria.

Se corre después de assemble.py, o suelto sobre data/nbu_db.json:

    python3 scripts/importar_capitulos_nn.py
    python3 scripts/inject_db.py
"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.path.join(BASE, "data", "capitulos_nn.json")
DB = os.path.join(BASE, "data", "nbu_db.json")

SECCION = "PMO_MED"
SECCION_LABEL = "Catálogo PMO — prestaciones médicas"
NOM_FULL = ("Catálogo de Prestaciones del PMO — Programa Médico Obligatorio "
            "(Resolución 201/2002, S.S. Salud)")


def ficha(c, cap, titulo, normas_cap, normas_sueltas, retirado=False, aviso=None):
    """Arma una ficha con la misma forma que las que ya están en la base.

       El valor NO va como U.B.: estos capítulos se arancelan por «unidades» de
       honorarios y gastos, que es otra unidad. Meterlos como U.B. haría que la
       app los multiplicara por el valor de la Unidad Bioquímica y mostrara un
       arancel inventado.

       `aviso` es la aclaración de a qué nomenclador pertenece el código, para
       los capítulos que se confunden con otro. La ficha la muestra arriba y el
       listado la muestra en el resultado: ver el capítulo 23.
    """
    aud = []
    if c.get("alcance"):
        aud.append("Alcance del Nomenclador Nacional: " + c["alcance"] + ".")
    if c.get("agregado_pmo"):
        aud.append("Código agregado por el P.M.O.")
    if retirado:
        # No es un detalle de archivo: significa que la práctica NO está en el
        # catálogo obligatorio, así que la ficha no puede decir que sí lo está.
        aud.append("⚠ Capítulo del Nomenclador Nacional RETIRADO POR EL P.M.O.: "
                   "la práctica existe en el Nacional pero quedó fuera del catálogo "
                   "de cobertura obligatoria. Confirmar contra el convenio aplicable.")
    for n in normas_cap:
        aud.append(n)
    if c["code"] in normas_sueltas:
        aud.append("Norma del código: " + normas_sueltas[c["code"]])
    if not retirado:
        aud.append("Prestación incluida en el Catálogo de Prestaciones del PMO — "
                   "cobertura obligatoria de los Agentes del Seguro de Salud (Res. 201/2002).")
    aud.append("Capítulo / especialidad: " + titulo + ".")

    partes = []
    if c.get("honorarios") is not None:
        partes.append("%s unidades de honorarios" % c["honorarios"])
    if c.get("gastos") is not None:
        partes.append("%s unidades de gastos" % c["gastos"])
    if c.get("total") is not None:
        partes.append("total práctica %s" % c["total"])
    if c.get("coseguro") is not None:
        partes.append("coseguro hasta %s" % c["coseguro"])
    arancel = ("Nomenclador Nacional: " + " · ".join(partes) + "."
               if partes else
               "Prestación del Catálogo del PMO (cobertura obligatoria). El arancel "
               "surge del nomenclador/convenio aplicable, no del NBU.")

    f = {
        "code": c["code"],
        "nomenclador": "PMO",
        "nomenclador_full": NOM_FULL,
        "seccion": SECCION,
        "seccion_label": SECCION_LABEL,
        "grupo": c.get("grupo") or titulo,
        "nombre": c["nombre"],
        # Los sinónimos entran al índice de búsqueda. Sirven para la ortografía
        # del original cuando la ficha lleva la corriente: el 23.02.34 está
        # impreso «TRANSPLANTE» y quien lo busque así tiene que encontrarlo.
        "sinonimos": c.get("sinonimos") or [],
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
        "en_catalogo_pmo": not retirado,
    }

    # La obligación de cobertura del catálogo. Va en su campo y no en auditoría
    # porque la app ya la sabe mostrar: cartel propio en la ficha y etiqueta en
    # el resultado del listado, que es donde se decide si se carga o no.
    if c.get("cobertura"):
        f["cobertura_pmo"] = c["cobertura"]
        f["cobertura_tipo"] = c.get("cobertura_tipo") or "obligacion"

    # A qué nomenclador pertenece el código, cuando se confunde con otro. Va en
    # la ficha Y en el listado a propósito: enterarse al abrir la ficha llega
    # tarde igual que con la observación administrativa.
    if aviso:
        f["aviso_nomenclador"] = aviso

    return f


def main():
    src = json.load(open(FUENTE, encoding="utf-8"))
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]
    nuevos = pisados = 0
    for cap, d in src["capitulos"].items():
        normas = d.get("norma", [])
        sueltas = d.get("normas_sueltas", {})
        for c in d["codigos"]:
            f = ficha(c, cap, d["titulo"], normas, sueltas,
                      retirado=bool(d.get("retirado_pmo")),
                      aviso=d.get("aviso_nomenclador"))
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
    print("capítulos %s: %d fichas nuevas, %d completadas"
          % (", ".join(sorted(src["capitulos"])), nuevos, pisados))
    print("total de códigos en la base:", len(cod))


if __name__ == "__main__":
    main()
