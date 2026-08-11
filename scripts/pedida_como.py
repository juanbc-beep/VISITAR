#!/usr/bin/env python3
"""Cómo puede venir escrita la práctica en la orden médica.

El médico escribe «CKMB» y en el manual la práctica figura como
«CREATINFOSFOQUINASA, ISOENZIMA MB». Quien atiende busca el nombre que le trajeron
y no encuentra nada, así que da por hecho que la práctica no está y la rechaza o
la carga con otro código.

Estos nombres alternativos salen del Excel de laboratorio de VISITAR, revisado
código por código por auditoría. **No cambian la denominación oficial**: se suman
como «puede venir solicitada como» y —lo que realmente resuelve el problema—
entran en el índice de búsqueda.

Algunos llevan además una aclaración: el Excel junta dos prácticas en un solo
renglón y son dos códigos distintos que se cargan por separado. Esa línea va a
auditoría, que es donde mira el que está decidiendo.

Hasta agosto de 2026 esto se aplicaba a mano sobre data/nbu_db.json y un armado
limpio lo borraba sin avisar. Por eso vive acá.

    from pedida_como import aplicar
    aplicar(records, log=sys.stderr)
"""
import json, os, sys


def _datos(base=""):
    for p in (os.path.join(base, "data/pedida_como.json"), "pedida_como.json"):
        try:
            return json.load(open(p, encoding="utf-8"))
        except FileNotFoundError:
            continue
    return {"codigos": {}}


def aplicar(records, log=None, base=""):
    doc = _datos(base)
    n = notas = falta = 0
    for code, d in (doc.get("codigos") or {}).items():
        r = records.get(code)
        if not r:
            falta += 1
            if log:
                print(f"  aviso: «pedida como» para {code}, que no está en la base", file=log)
            continue
        nombres = [x for x in (d.get("pedida_como") or []) if x and x.strip()]
        if nombres:
            ya = list(r.get("pedida_como") or [])
            for x in nombres:
                if x not in ya:
                    ya.append(x)
            r["pedida_como"] = ya
            n += 1
        nota = (d.get("nota") or "").strip()
        if nota:
            r.setdefault("auditoria", [])
            if nota not in r["auditoria"]:
                r["auditoria"].insert(0, nota)
            notas += 1
    if log:
        print(f"«Puede venir solicitada como»: {n} códigos · aclaraciones {notas}"
              + (f" · sin ficha en la base {falta}" if falta else ""), file=log)
    return n


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/nbu_db.json"
    db = json.load(open(ruta, encoding="utf-8"))
    aplicar(db["codigos"], log=sys.stderr)
    json.dump(db, open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
    print("escrito " + ruta, file=sys.stderr)
