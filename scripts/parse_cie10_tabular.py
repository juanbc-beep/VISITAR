#!/usr/bin/env python3
"""Parse the official CIE-10 tabular list (OMS, ES) volumes and MERGE code->title into cie10.json.
Handles multi-line wrapped titles; ignores Incluye/Excluye notes and page furniture."""
import json, re, sys
import pdfplumber

OUT = "data/cie10.json"
PDFS = sys.argv[1:]

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

CODE=re.compile(r'^([A-Z]\d{2}(?:\.\d{1,2})?)[\*†]?\s+(.+)$')
ANYCODE=re.compile(r'^[A-Z]\d{2}(?:\.\d{1,2})?[\*†]?\s')

def is_cont(l):
    """Line is a wrapped continuation of a title (starts lowercase / connector)."""
    if not l or ANYCODE.match(l): return False
    c=l[0]
    return c.islower() or c.isdigit() or c in ',/-'

found={}
for f in PDFS:
    with pdfplumber.open(f) as pdf:
        for pg in pdf.pages:
            lines=[x.rstrip() for x in (pg.extract_text() or '').split('\n')]
            i=0
            while i<len(lines):
                ln=lines[i].strip()
                m=CODE.match(ln)
                if m:
                    code=m.group(1); desc=m.group(2).strip()
                    j=i+1; k=0
                    while j<len(lines) and k<3 and is_cont(lines[j].strip()):
                        desc+=' '+lines[j].strip(); j+=1; k+=1
                    desc=re.sub(r'\s+',' ',desc).strip(' .')
                    # ignore obvious note fragments captured as code (rare)
                    if 2<len(desc)<200:
                        if code not in found or len(desc)>len(found[code]):
                            found[code]=desc
                    i=j
                else:
                    i+=1

data=json.load(open(OUT, encoding="utf-8"))
cod=data["codigos"]
added=upd=0
for code,desc in found.items():
    rom,cap=chapter(code)
    if code in cod:
        # oficial: preferir el título más largo/limpio
        if len(desc)>len(cod[code].get("desc","")):
            cod[code]["desc"]=desc; cod[code]["cap"]=rom; cod[code]["cap_nombre"]=cap; upd+=1
    else:
        rec={"code":code,"desc":desc,"cap":rom,"cap_nombre":cap}
        if len(code)>3: rec["parent"]=code[:3]; rec["sub"]=True
        cod[code]=rec; added+=1
json.dump(data, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"tabular: parseados {len(found)} · nuevos {added} · actualizados {upd} · total ahora {len(cod)}", file=sys.stderr)
