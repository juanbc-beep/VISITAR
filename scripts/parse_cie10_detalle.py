#!/usr/bin/env python3
"""Merge the detailed CIE-10-ES subcategory codes (from the 3-part clinical manual) into cie10.json.
The manual is a narrative guide with coding examples; we extract every 'CODE  description' line."""
import json, re, sys
import pdfplumber

OUT = "data/cie10.json"
PDFS = sys.argv[1:] or []

CAPS = [
    ("I","Ciertas enfermedades infecciosas y parasitarias",[("A",0,99),("B",0,99)]),
    ("II","Tumores (neoplasias)",[("C",0,99),("D",0,48)]),
    ("III","Enf. de la sangre y de los órganos hematopoyéticos",[("D",50,89)]),
    ("IV","Enf. endocrinas, nutricionales y metabólicas",[("E",0,90)]),
    ("V","Trastornos mentales y del comportamiento",[("F",0,99)]),
    ("VI","Enf. del sistema nervioso",[("G",0,99)]),
    ("VII","Enf. del ojo y sus anexos",[("H",0,59)]),
    ("VIII","Enf. del oído y de la apófisis mastoides",[("H",60,95)]),
    ("IX","Enf. del sistema circulatorio",[("I",0,99)]),
    ("X","Enf. del sistema respiratorio",[("J",0,99)]),
    ("XI","Enf. del sistema digestivo",[("K",0,95)]),
    ("XII","Enf. de la piel y del tejido subcutáneo",[("L",0,99)]),
    ("XIII","Enf. del sistema osteomuscular y tejido conjuntivo",[("M",0,99)]),
    ("XIV","Enf. del sistema genitourinario",[("N",0,99)]),
    ("XV","Embarazo, parto y puerperio",[("O",0,99)]),
    ("XVI","Afecciones originadas en el período perinatal",[("P",0,96)]),
    ("XVII","Malformaciones congénitas y anomalías cromosómicas",[("Q",0,99)]),
    ("XVIII","Síntomas, signos y hallazgos anormales (clínicos y de laboratorio)",[("R",0,99)]),
    ("XIX","Traumatismos, envenenamientos y causas externas",[("S",0,99),("T",0,98)]),
    ("XX","Causas externas de morbilidad y mortalidad",[("V",1,99),("W",0,99),("X",0,99),("Y",0,98)]),
    ("XXI","Factores que influyen en el estado de salud (contacto con servicios)",[("Z",0,99)]),
    ("XXII","Códigos para propósitos especiales",[("U",0,99)]),
]
def chapter(code):
    L=code[0]; n=int(code[1:3])
    for rom,name,ranges in CAPS:
        for (l,lo,hi) in ranges:
            if l==L and lo<=n<=hi: return rom,name
    return "?","Sin clasificar"

CODE=re.compile(r'^([A-Z]\d{2}(?:\.[0-9A-Z]{1,4})?)\s+(\S.{3,})$')
BAD=re.compile(r'(unidad técnica|capítulo|p[aá]gina|www|cie-\d|ministerio)', re.I)

found={}
for f in PDFS:
    with pdfplumber.open(f) as pdf:
        for pg in pdf.pages:
            for ln in (pg.extract_text() or '').split('\n'):
                m=CODE.match(ln.strip())
                if not m: continue
                code=m.group(1); desc=" ".join(m.group(2).split())
                if BAD.search(desc): continue
                # trim trailing example noise: keep up to ~140 chars, cut at 2nd sentence
                desc=re.sub(r'\s+',' ',desc)[:160].strip()
                if code not in found or len(desc)>len(found[code]):
                    found[code]=desc

# merge into existing cie10.json
data=json.load(open(OUT, encoding="utf-8"))
cod=data["codigos"]
added=0
for code,desc in found.items():
    rom,cap=chapter(code)
    sub=len(code)>3
    if code in cod:
        # keep existing category title for 3-char; don't overwrite
        continue
    cod[code]={"code":code,"desc":desc,"cap":rom,"cap_nombre":cap}
    if sub:
        cod[code]["parent"]=code[:3]; cod[code]["sub"]=True
    added+=1
json.dump(data, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"CIE-10 detalle: extraídos {len(found)} · agregados nuevos {added} · total ahora {len(cod)}", file=sys.stderr)
