#!/usr/bin/env python3
"""Seed curado de relaciones CIE-10 -> prácticas (NBU/PMO), resueltas por nombre contra la base."""
import json, sys, unicodedata

DB = json.load(open("data/nbu_db.json", encoding="utf-8"))["codigos"]
CIE = json.load(open("data/cie10.json", encoding="utf-8"))

def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    return s

# índice nombre -> code (solo NBU + PMO médicos, prácticas reales)
IDX = [(norm(v["nombre"]), k, v) for k, v in DB.items() if v.get("nomenclador") in ("NBU", "PMO")]

def find(*terms, n=6):
    """Devuelve códigos cuyas prácticas contienen TODOS los términos (por variante); prioriza NBU."""
    out = []
    for hay, k, v in IDX:
        if all(t in hay for t in terms):
            out.append((0 if v["nomenclador"] == "NBU" else 1, v["code"], k))
    out.sort()
    seen, res = set(), []
    for _, code, k in out:
        if code not in seen:
            seen.add(code); res.append(code)
        if len(res) >= n:
            break
    return res

# cada CIE -> lista de grupos de búsqueda (se unen los resultados, en orden)
SEED = {
    "E10": [["glucemia"], ["hemoglobina glicosilada"], ["insulina"], ["tolerancia", "glucosa"], ["fructosamina"], ["microalbuminuria"]],
    "E11": [["glucemia"], ["hemoglobina glicosilada"], ["insulina"], ["tolerancia", "glucosa"], ["fructosamina"], ["microalbuminuria"]],
    "E14": [["glucemia"], ["hemoglobina glicosilada"]],
    "O24": [["glucemia"], ["tolerancia", "glucosa"], ["hemoglobina glicosilada"]],
    "E03": [["tsh"], ["t4 libre"], ["tiroxina"], ["t3"]],
    "E02": [["tsh"], ["t4 libre"]],
    "E05": [["tsh"], ["t4 libre"], ["t3"], ["tiroglobulina"], ["tpo"]],
    "E06": [["tpo"], ["antitiroglobulina"], ["tiroglobulina"]],
    "E78": [["colesterol total"], ["colesterol hdl"], ["colesterol ldl"], ["trigliceridos"]],
    "E88": [["colesterol total"], ["trigliceridos"]],
    "D50": [["hemograma"], ["ferritina"], ["ferremia"], ["transferrina"], ["saturacion"]],
    "D51": [["vitamina b12"], ["acido folico"], ["hemograma"]],
    "D52": [["acido folico"], ["vitamina b12"], ["hemograma"]],
    "D64": [["hemograma"], ["reticulocitos"], ["ferritina"]],
    "B18": [["hbsag"], ["antigeno de superficie"], ["hepatitis c"], ["hepatograma"], ["transaminasas"], ["tgo"], ["tgp"]],
    "B16": [["hbsag"], ["antigeno de superficie"], ["hepatitis b"], ["hepatograma"]],
    "B17": [["hepatitis c"], ["hepatitis a"], ["hepatograma"]],
    "B19": [["hepatograma"], ["transaminasas"]],
    "B20": [["hiv"], ["carga viral"], ["cd4"], ["poblaciones linfocitarias"]],
    "B24": [["hiv"], ["carga viral"], ["cd4"]],
    "Z21": [["hiv"], ["carga viral"], ["cd4"]],
    "N18": [["creatinina"], ["urea"], ["clearance"], ["filtrado glomerular"], ["ionograma"]],
    "N17": [["creatinina"], ["urea"], ["ionograma"]],
    "K90": [["transglutaminasa"], ["endomisio"], ["gliadina"], ["celiaquia"]],
    "N97": [["fsh"], ["lh"], ["estradiol"], ["progesterona"], ["prolactina"], ["antimulleriana"]],
    "N46": [["espermograma"], ["fsh"], ["lh"], ["testosterona"], ["prolactina"]],
    "E28": [["fsh"], ["lh"], ["testosterona"], ["androstenediona"], ["17"], ["prolactina"]],
    "E66": [["glucemia"], ["insulina"], ["colesterol total"], ["trigliceridos"], ["tsh"]],
    "I10": [["creatinina"], ["ionograma"], ["orina completa"], ["colesterol total"]],
    "M81": [["vitamina d"], ["calcio"], ["parathormona"], ["fosfatasa alcalina"]],
    "M80": [["vitamina d"], ["calcio"], ["parathormona"]],
    "E55": [["vitamina d"], ["calcio"], ["fosforo"]],
    "N39": [["urocultivo"], ["orina completa"], ["sedimento"]],
    "N30": [["urocultivo"], ["orina completa"]],
    "D68": [["coagulograma"], ["tiempo de protrombina"], ["kptt"], ["fibrinogeno"]],
    "E27": [["cortisol"], ["acth"], ["aldosterona"]],
    "E24": [["cortisol"], ["acth"]],
    "C61": [["psa"], ["antigeno prostatico"]],
    "E05.9": [["tsh"]],
    "R73": [["glucemia"], ["tolerancia", "glucosa"], ["hemoglobina glicosilada"]],
    "R77": [["proteinograma"], ["inmunoglobulinas"]],
    "D86": [["enzima convertidora"], ["calcio"]],
    "M32": [["anticuerpos antinucleares"], ["ana"], ["anti dna"], ["complemento"]],
    "M05": [["factor reumatoideo"], ["anticuerpos anti peptido"], ["proteina c reactiva"], ["eritrosedimentacion"]],
    "M06": [["factor reumatoideo"], ["proteina c reactiva"], ["eritrosedimentacion"]],
}

rel = {}
for cie, groups in SEED.items():
    codes = []
    for g in groups:
        for c in find(*g, n=3):
            if c not in codes:
                codes.append(c)
    if codes:
        rel[cie] = codes[:8]

CIE["relaciones"] = rel
json.dump(CIE, open("data/cie10.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"CIE con relaciones curadas: {len(rel)}", file=sys.stderr)
for k in ["E11", "E03", "K90", "N97", "D50", "B20"]:
    print(" ", k, "->", rel.get(k), file=sys.stderr)
