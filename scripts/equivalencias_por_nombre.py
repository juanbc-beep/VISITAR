#!/usr/bin/env python3
"""Equivalencias que la planilla del Único declara con un número que no existe,
y que se resuelven mirando el NOMBRE.

Y, de paso, devuelve el texto que la planilla traía en `desc` y que un script
anterior había pisado con el nombre del destino.

────────────────────────────────────────────────────────────────────────────
Lo que hay detrás de estos casos
────────────────────────────────────────────────────────────────────────────

El Nomenclador Único lista las prácticas de laboratorio **varias veces**, en
bloques con prefijo 60, 61, 62, 63 y 64. En muchos casos la misma práctica
aparece en dos bloques: una fila con el número correcto del NBU y otra con un
número que no existe, y los nombres difieren sólo en acentos o puntuación:

    64662384 «ÁCIDOS ORGÁNICOS»  → 662384  ✓ atada
    64662389 «ACIDOS ORGANICOS»  → 662389  ✗ ese número no existe

La segunda no es una práctica que falte: es **la misma fila repetida**. Se ata
igual —quien mire esa ficha del Único tiene que llegar al 662384 y no leer «no
está cargada todavía»—, pero **no se agrega el reflejo** en la ficha del NBU:
esa ficha ya muestra la fila canónica, y sumarle una segunda casi idéntica haría
creer que hay dos códigos facturables cuando hay uno.

⚠️ NO se ata por parecido de nombre a secas. Cada par de abajo se miró de a uno.
Dos quedaron afuera y vale la pena saber por qué:

  · HIDATIDOSIS (IFI) — el catálogo tiene el mismo nombre en 660484 y 661100, y
    los dos ya están tomados por otras técnicas del Único (látex, 10 U.B., y
    arco 5, 22 U.B.). La del Único es una tercera. Sin datos para elegir.

  · DOMICILIO «Más de 2 Kms» contra «Hasta 2 Kms», y BCR/ABL «LMC» contra
    «LLA» — nombres casi iguales, prácticas opuestas.

⚠️ CHAGAS (PCR) descubre un error que YA ESTABA en la base y que este script no
toca, porque corregirlo es decisión de los médicos: la fila 63663576 del Único
se llama «CHAGAS, Ac. Totales Anti- (ELISA)» y está atada al NBU 663576, que es
«CHAGAS, (PCR)». El ELISA del NBU es el 663580, y ya lo reclama —bien— la fila
64663580. O sea que 63663576 está apuntando a la práctica equivocada.

Todo lo que se ata queda con `recalculada: "nombre"`, que es la marca que la
ficha ya sabe mostrar: «⚠ El código que traía la planilla no existe… se
reconstruyó por proximidad de nombre — conviene confirmarla».

Los nombres de las fichas NO se tocan, de ningún lado: cada nomenclador dice lo
que dice y así queda.

    python3 scripts/equivalencias_por_nombre.py
    python3 scripts/inject_db.py
"""
import json, os, subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "nbu_db.json")

# Commit anterior a que `reparar_equivalencias.py` pisara los `desc`.
COMMIT_PREVIO = "e3c9036"

# (clave del Único, código real, reflejo en la ficha del destino)
#   reflejo=False → la práctica ya está representada en esa ficha por la fila
#   canónica del Único; ésta es la fila repetida del otro bloque.
PARES = [
    # ── repetidas: difieren en acentos o puntuación de una fila ya atada
    ("U64662389", "662384", False),   # ÁCIDOS ORGÁNICOS
    ("U64662492", "662478", False),   # ALFA 1 ANTITRIPSINA, líquido pleural
    ("U64662927", "662922", False),   # BENCENO, urinario
    ("U64663817", "663811", False),   # COBRE, plasmático
    ("U64663962", "663965", False),   # COPROPORFIRINAS, materia fecal
    ("U64667030", "667025", False),   # LEUCINAS AGUDAS, fenotipificación
    ("U64667235", "667238", False),   # LISTERIA MONOCITÓGENES "O" y "H"
    ("U64669635", "669605", False),   # TRANSLOCACIÓN 14;18
    ("U64669773", "669776", False),   # UROPORFIRINAS, urinarias
    ("U64667716", "661140", False),   # MYCOPLASMA PNEUMONIAE IgG (fila del bloque 61)

    # ── prácticas propias: el destino no las tenía representadas
    ("U64663581", "663576", True),    # CHAGAS (PCR) → el NBU 663576 ES el PCR
    ("U40270201", "270201", True),    # evaluación pretrasplante renal en receptor
    ("U40270202", "270202", True),    # evaluación pretrasplante renal en dador
]


def descs_originales():
    """El `desc` que traía la planilla, tal como estaba antes de pisarlo."""
    try:
        crudo = subprocess.run(
            ["git", "show", "%s:data/nbu_db.json" % COMMIT_PREVIO],
            cwd=BASE, capture_output=True, check=True).stdout
    except Exception as e:
        print("  ⚠ no se pudo leer el commit %s (%s): no se devuelven los desc"
              % (COMMIT_PREVIO, e))
        return {}
    viejo = json.loads(crudo)["codigos"]
    return {k: (v.get("equivalencia") or {}).get("desc")
            for k, v in viejo.items() if v.get("equivalencia")}


def main():
    db = json.load(open(DB, encoding="utf-8"))
    cod = db["codigos"]
    nombres_antes = {k: v.get("nombre") for k, v in cod.items()}

    # ── 1. recuperar la redacción de la planilla ──────────────────────────
    #
    # `desc` es lo que la ficha imprime debajo de «Equivale a NNNNNN», así que
    # ahí tiene que ir el nombre del destino: es el que el lector necesita para
    # saber adónde lo mandan. Lo que no puede perderse es cómo llamaba la
    # planilla del Único a esa práctica, que es un texto distinto y a veces
    # revelador —«PERFUSION CARDIACA CON RADIOISOTOPICA» contra «Perfusión
    # sanguínea miocárdica con radioisótopos»—. Va a `desc_declarada`, y la
    # ficha la muestra cuando difiere.
    orig = descs_originales()
    devueltos = 0
    for k, d in orig.items():
        v = cod.get(k)
        if not v or not d:
            continue
        e = v.get("equivalencia")
        if not e or e.get("desc") == d or e.get("desc_declarada"):
            continue
        e["desc_declarada"] = d
        devueltos += 1
    print("redacciones de la planilla recuperadas: %d" % devueltos)

    # ── 2. atar por nombre ────────────────────────────────────────────────
    hechas = reflejos = 0
    for uk, destino, reflejo in PARES:
        v, r = cod.get(uk), cod.get(destino)
        if not v or not r:
            print("  ⚠ falta %s o %s" % (uk, destino))
            continue
        e = v.get("equivalencia") or {}
        declarado = e.get("code")

        e["code_declarado"] = declarado
        e.setdefault("desc_declarada", e.get("desc"))
        e["code"] = destino
        e["key"] = destino
        e["desc"] = r.get("nombre")          # el nombre que el destino tiene, sin tocarlo
        e["recalculada"] = "nombre"
        e.pop("destino_inexistente", None)
        v["equivalencia"] = e

        nota = ("Equivalencia: la planilla del Nomenclador Único declara el código "
                "%s, que no existe. Se ató al %s por coincidencia de nombre — "
                "conviene que un médico la confirme." % (declarado, destino))
        for c in (v, r):
            aud = c.setdefault("auditoria", [])
            if nota not in aud:
                aud.append(nota)

        if reflejo:
            lista = r.setdefault("equivalencia_unico", [])
            if not any(x.get("unico_key") == uk for x in lista):
                lista.append({
                    "unico_code": v.get("code") or uk.lstrip("U"),
                    "unico_key": uk,
                    "unico_desc": v.get("nombre") or "",
                    "score": e.get("score"),
                    "tipo": "lab" if r.get("nomenclador") == "NBU" else "med",
                })
                reflejos += 1
        hechas += 1
        print("  ✔ %s → %s%s  (la planilla decía %s)"
              % (uk, destino, "" if reflejo else "  [fila repetida, sin reflejo]",
                 declarado))

    # ── 3. la garantía: ningún nombre de ficha se movió ───────────────────
    movidos = [k for k, n in nombres_antes.items() if cod[k].get("nombre") != n]
    if movidos:
        raise SystemExit("✗ se modificaron nombres de ficha: %s" % movidos[:5])
    print("nombres de ficha intactos: %d verificados" % len(nombres_antes))

    json.dump(db, open(DB, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("equivalencias atadas: %d · reflejos agregados: %d" % (hechas, reflejos))


if __name__ == "__main__":
    main()
