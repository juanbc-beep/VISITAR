#!/usr/bin/env python3
"""Parse the PMO (Res. 201/2002), column-aware, ALL anexos:
- ANEXO I : generalidades (todas las secciones) + topes (límites de cobertura)
- ANEXO II: código 6 díg -> {titulo limpio, cobertura}
- ANEXO III: reglas del Formulario Terapéutico (generalidades)
- ANEXO IV: vademécum -> medicamentos {atc, nombre, grupo}"""
import json, re, sys
import pdfplumber

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/pmo.pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/pmo_cobertura.json"

def col_lines(pg):
    w = pg.width; mid = w/2
    words = pg.extract_words(use_text_flow=False)
    def lines(ws):
        ws = sorted(ws, key=lambda z: (round(z['top']/3), z['x0']))
        out=[]; cur=[]; ct=None
        for z in ws:
            if ct is None or abs(z['top']-ct) < 4: cur.append(z['text'])
            else: out.append(' '.join(cur)); cur=[z['text']]
            ct=z['top']
        if cur: out.append(' '.join(cur))
        return out
    L=[x for x in words if (x['x0']+x['x1'])/2 < mid]
    R=[x for x in words if (x['x0']+x['x1'])/2 >= mid]
    return lines(L)+lines(R)

pdf = pdfplumber.open(SRC)
anexo_of = {}; cur = 0
for pi in range(len(pdf.pages)):
    t = pdf.pages[pi].extract_text() or ""
    for a in [1,2,3,4]:
        if re.search(r'ANEXO %s\b' % {1:'I',2:'II',3:'III',4:'IV'}[a], t):
            cur = max(cur, a)
    anexo_of[pi] = cur
def lines_of(anx):
    out=[]
    for pi in range(len(pdf.pages)):
        if anexo_of[pi]==anx: out += col_lines(pdf.pages[pi])
    return out

# ---- ANEXO II ----
CODE = re.compile(r'^(\d{6})\s+(.+)$')
def is_cont(l): return l and not CODE.match(l) and (l[0].islower() or l[0] in '(,')
codigos = {}; L2 = lines_of(2); i=0
while i < len(L2):
    ln = L2[i].strip(); m = CODE.match(ln)
    if m:
        code=m.group(1); title=m.group(2).strip(); j=i+1
        while j<len(L2) and is_cont(L2[j].strip()) and not L2[j].strip().startswith('•'):
            title += ' '+L2[j].strip(); j+=1
        cob=[]
        while j<len(L2) and not CODE.match(L2[j].strip()):
            s=L2[j].strip()
            if s: cob.append(s)
            j+=1
        title=re.sub(r'\s+',' ',title).strip(' .')
        cobertura=re.sub(r'^•\s*','',re.sub(r'\s+',' ',' '.join(cob)).strip())
        if code not in codigos or len(title)<len(codigos[code]['titulo']):
            codigos[code]={"titulo":title,"cobertura":cobertura if len(cobertura)>8 else ""}
        i=j
    else: i+=1

def blob_of(anx):
    b="\n".join(lines_of(anx)); b=re.sub(r'-\n','',b); b=re.sub(r'\n',' ',b); return re.sub(r'\s+',' ',b)

# ---- ANEXO I + III : generalidades ----
gener=[]
SEC = re.compile(r'(?:^|\s)(\d(?:\.\d){0,2})\.?\s+([A-ZÁÉÍÓÚ][^:.]{3,45}):')
def sections(blob, fuente):
    marks=list(SEC.finditer(blob))
    for idx,mm in enumerate(marks):
        num=mm.group(1); titulo=mm.group(2).strip(); start=mm.end()
        end=marks[idx+1].start() if idx+1<len(marks) else len(blob)
        texto=blob[start:end].strip()
        if 3<len(texto):
            gener.append({"num":num,"titulo":titulo,"texto":texto[:1600],"fuente":fuente})
b1=blob_of(1); sections(b1,"Anexo I")
# Anexo III: solo el texto introductorio (antes del listado ATC de medicamentos)
ATC0 = re.compile(r'^[A-Z]\d{2}[A-Z]{0,2}\d{0,2}\s')
intro3=[]
for ln in lines_of(3):
    if ATC0.match(ln.strip()): break
    intro3.append(ln)
b3=re.sub(r'\s+',' ',re.sub(r'-\n','',' '.join(intro3))).strip()
if len(b3)>40:
    gener.append({"num":"III","titulo":"Formulario Terapéutico — reglas","texto":b3[:1600],"fuente":"Anexo III"})

# ---- topes: oraciones con cantidad + palabra de límite/cobertura ----
LIMIT = re.compile(r'(sesiones|visitas|consultas|veces|año|años|edad|cobertura|cubrir|cubrirá|%|meses|mensuales)', re.I)
QTY = re.compile(r'(hasta|\d+|una vez|dos veces|100\s*%|primer|único)', re.I)
topes=[]; seen=set()
for sent in re.split(r'(?<=[.])\s+', b1):
    s=sent.strip()
    if 15<len(s)<220 and QTY.search(s) and LIMIT.search(s) and re.search(r'\d', s):
        key=s[:40]
        if key not in seen: seen.add(key); topes.append(s)

# ---- ANEXO IV : vademécum ----
ATC = re.compile(r'^([A-Z]\d{2}[A-Z]{0,2}\d{0,2})\s+(.+)$')
GRP1 = re.compile(r'^([A-Z])\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ ,/]{4,})$')
meds=[]; L4=lines_of(3)+lines_of(4); grupo=""; seen_atc=set(); i=0
while i<len(L4):
    ln=L4[i].strip()
    g=GRP1.match(ln)
    if g and ln.isupper():
        grupo=g.group(2).title(); i+=1; continue
    m=ATC.match(ln)
    if m and not ln.isupper():
        atc=m.group(1); nombre=m.group(2).strip(); j=i+1
        while j<len(L4) and L4[j].strip() and L4[j].strip()[0].islower() and not ATC.match(L4[j].strip()):
            nombre+=' '+L4[j].strip(); j+=1
        nombre=re.sub(r'\s+',' ',nombre).strip(' .')
        key=atc+nombre[:12]
        if key not in seen_atc:
            seen_atc.add(key); meds.append({"atc":atc,"nombre":nombre,"grupo":grupo})
        i=j
    else: i+=1

# fallback de grupo por primera letra ATC
ATCG = {"A":"Aparato digestivo y metabolismo","B":"Sangre y hematopoyesis","C":"Aparato cardiovascular",
        "D":"Dermatológicos","G":"Genitourinario y hormonas sexuales","H":"Hormonas sistémicas",
        "J":"Antiinfecciosos (uso sistémico)","L":"Antineoplásicos e inmunomoduladores","M":"Aparato locomotor",
        "N":"Sistema nervioso","P":"Antiparasitarios","R":"Aparato respiratorio","S":"Órganos de los sentidos","V":"Varios"}
for m in meds:
    if not m["grupo"]:
        m["grupo"] = ATCG.get(m["atc"][0], "Otros")
json.dump({"codigos":codigos,"generalidades":gener,"topes":topes,"medicamentos":meds},
          open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"PMO: códigos {len(codigos)} · cobertura {sum(1 for v in codigos.values() if v['cobertura'])} · generalidades {len(gener)} · topes {len(topes)} · medicamentos {len(meds)}", file=sys.stderr)
