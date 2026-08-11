#!/usr/bin/env python3
"""Da de alta los códigos del capítulo 34 que faltaban por completo en la base.

El Catálogo de Prestaciones del PMO no imprime todas las prestaciones del capítulo
34: las exposiciones subsiguientes de radiología —el código que se cobra por cada
placa adicional— y otras 17 figuran en el Nomenclador Nacional con la leyenda
«Texto retirado por el PMO». Como el armado sale del catálogo, esos códigos no
existían en ningún lado de la app: ni se encontraban buscando, ni aparecían al
cargar un caso, y las equivalencias del Único apuntaban al vacío.

Existen como prestación aunque el PMO no las incluya, y quien atiende necesita
poder mirarlas: por eso se dan de alta, y por eso cada ficha dice en la primera
línea de auditoría que el PMO no la incluye. Ocultarlas sería peor —el agente no
encuentra el código y cree que no existe— y mostrarlas sin la aclaración también
—lo carga creyendo que tiene cobertura obligatoria—.

La denominación se transcribe del OCR del Nacional, que en esta parte está
dañado. Las que el Único trae en su planilla se contrastaron contra ella y quedan
firmes; las que dependen sólo del OCR quedan marcadas «denominación a confirmar»,
con el texto original guardado en la ficha para poder corregirlo sin abrir el PDF.

    from altas_pmo_cap34 import altas
    altas(records, log=sys.stderr)
"""
import json, os, sys

GRUPO = "Radiología / Diagnóstico por imágenes"
LEYENDA = ("Figura en el Nomenclador Nacional con la leyenda «Texto retirado por el PMO»: "
           "el Catálogo de Prestaciones del PMO no la incluye.")


def _datos(base=""):
    for p in (os.path.join(base, "data/pmo_cap34_faltantes.json"), "pmo_cap34_faltantes.json"):
        try:
            return json.load(open(p, encoding="utf-8"))
        except FileNotFoundError:
            continue
    return {"codigos": {}}


def altas(records, log=None, base=""):
    doc = _datos(base)
    n = eq = 0
    for code, d in (doc.get("codigos") or {}).items():
        if code in records:
            continue
        r = {
            "code": code, "nomenclador": "PMO",
            "nomenclador_full": "Nomenclador Nacional de Prestaciones Médicas (Res. 201/02) — no incluida en el Catálogo del PMO",
            "seccion": "PMO_MED", "seccion_label": "Catálogo PMO — prestaciones médicas",
            "grupo": GRUPO, "nombre": d["nombre"],
            "sinonimos": [], "abreviaturas": [],
            "valor": {"ub": None, "unidad": "—",
                      "arancel": "El Nomenclador Nacional no trae valorización para esta prestación. El arancel surge del convenio aplicable."},
            "flags": {"urgencia": False, "requiere_norma": False, "desuso": False, "pcr": False},
            "referencias": [], "norma": None, "frecuencia": [],
            "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
            "auditoria": [LEYENDA],
            "fuera_catalogo_pmo": True,
        }
        # De cuál práctica es la exposición siguiente. El Nacional lo dice a su
        # manera: imprime el nombre completo en el código impar con «primera
        # exposición» al final, y en el par sólo «por exposición subsiguiente».
        # Nueve códigos con el mismo nombre no le sirven a nadie en un listado,
        # así que la denominación se compone con la práctica que la precede y la
        # ficha explica de dónde sale cada parte.
        if d.get("sigue_a"):
            ant = records.get(d["sigue_a"])
            cola = (" y su denominación se compone con la de esa práctica."
                    if d.get("nombre_practica") else ".")
            # El guión de cierre sólo si sigue texto: si no, la línea terminaba
            # en « — .», que se lee como un renglón cortado.
            r["auditoria"].append(
                "En el Nomenclador Nacional viene a continuación de " + d["sigue_a"] +
                (" — " + ant["nombre"] + (" —" if cola != "." else "") if ant else "") +
                cola)
            if ant:
                r["relaciones"]["incluido_en"] = [d["sigue_a"]]
        if d.get("titulo_revisar"):
            r["titulo_revisar"] = True
            if d.get("ocr"):
                # El texto tal como salió del OCR, para poder corregir la
                # denominación desde la ficha sin ir a buscar el original.
                r["titulo_origen"] = d["ocr"]
        records[code] = r
        n += 1
        # La equivalencia con el Único quedaba colgando: apuntaba a un código que
        # no existía. Ahora existe, así que se ata de los dos lados.
        u = records.get("U" + code)
        if u and isinstance(u.get("equivalencia"), dict) and u["equivalencia"].get("code") == code:
            u["equivalencia"]["key"] = code
            u["sin_equivalencia"] = False
            r["equivalencia_unico"] = [{"unico_code": code, "unico_key": "U" + code,
                                        "unico_desc": u["nombre"], "score": None, "tipo": "med"}]
            eq += 1
    if log:
        print(f"PMO capítulo 34: prestaciones dadas de alta desde el Nacional {n} · "
              f"equivalencias del Único resueltas {eq}", file=log)
    return n


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/nbu_db.json"
    db = json.load(open(ruta, encoding="utf-8"))
    altas(db["codigos"], log=sys.stderr)
    json.dump(db, open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
    print("escrito " + ruta, file=sys.stderr)
