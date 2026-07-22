#!/usr/bin/env python3
"""SURGE — Sistema Único de Reintegro por Gestión de Enfermedades (Res. 731/2023, Anexo II).
Parsea el PDF COMPLETO (67 págs): recorre todas las secciones del índice y captura su
contenido estructurado — tecnología, fundamento terapéutico, información requerida,
sub-módulos (A./B./...), prestaciones/prótesis incluidas, observaciones, empadronamiento,
actualización semestral, etc. Cruza con:
  - el Excel (medicación SURGE + requerimiento de autorización que pide VISITAR),
  - los códigos del nomenclador marcados (SUR)/(SURGE),
  - diagnósticos CIE-10.
Genera data/surge.json."""
import json, re, sys, zipfile, unicodedata
import xml.etree.ElementTree as ET
import pdfplumber

PDF = sys.argv[1] if len(sys.argv) > 1 else "data/surge.pdf"
ODS = sys.argv[2] if len(sys.argv) > 2 else "data/surge.ods"
OUT = sys.argv[3] if len(sys.argv) > 3 else "data/surge.json"

def nk(s):
    s = unicodedata.normalize('NFD', s).encode('ascii','ignore').decode().upper()
    return re.sub(r'[^A-Z0-9]', '', s)

# ---------- 1) Excel: medicación + requerimiento VISITAR ----------
T = '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
def read_ods(path):
    z = zipfile.ZipFile(path); root = ET.fromstring(z.read('content.xml'))
    table = next(root.iter(T+'table')); rows = []
    for r in table.iter(T+'table-row'):
        vals = []
        for c in r.findall(T+'table-cell'):
            rep = int(c.get(T+'number-columns-repeated','1'))
            vals.extend([''.join(t for t in c.itertext())]*min(rep,10))
        while vals and vals[-1] == '': vals.pop()
        rows.append(vals)
    return rows

def split_items(s):
    if not s: return []
    s = re.sub(r'\s+',' ',s.replace('\n',' ')).strip()
    s = re.sub(r'^[-*]\s*','',s)
    parts = re.split(r'\s*[-*]\s+(?=[A-ZÁÉÍÓÚÑ])', s)
    out = []
    for p in parts:
        p = re.sub(r'\s+',' ',p).strip(' -*.,')
        if len(p) >= 2: out.append(p)
    return out

excel = {}
try:
    for r in read_ods(ODS):
        if len(r) >= 2 and r[0] and nk(r[0]) not in ('PATOLOGIA',) and 'SISTEMAUNICO' not in nk(r[0]):
            excel[nk(r[0])] = {"medicacion": split_items(r[1] if len(r)>1 else ''),
                               "requerimiento_visitar": split_items(r[2] if len(r)>2 else '')}
except FileNotFoundError:
    print("aviso: no se encontró el Excel SURGE", file=sys.stderr)

# ---------- 2) PDF: secciones e índice ----------
# títulos del índice (patologías + encabezados de especialidad)
TITLES = ["ONCOLOGÍA","CÁNCER DE MAMA","CÁNCER DE COLON","CÁNCER DE PRÓSTATA","CÁNCER DE PULMÓN",
"CÁNCER DE RIÑÓN","MELANOMA","MÓDULO DE RADIOTERAPIA ONCOLÓGICA","ONCOHEMATOLOGÍA","MIELOMA MÚLTIPLE",
"LEUCEMIA MIELOIDE CRÓNICA (LMC)","REUMATOLOGÍA","ARTRITIS REUMATOIDEA","ARTRITIS PSORIÁSICA","PSORIASIS EN PLACA",
"ARTRITIS IDIOPÁTICA JUVENIL SISTÉMICA (AIJS)","ESPONDILITIS ANQUILOSANTE-ESPONDILITIS AXIAL NO RADIOGRÁFICA",
"ENFERMEDAD INFLAMATORIA INTESTINAL","ENFERMEDAD DE CROHN","COLITIS ULCEROSA","ENFERMEDADES LISOSOMALES",
"ENFERMEDAD DE FABRY (EF)","ENFERMEDAD DE GAUCHER (EG)","ENFERMEDAD DE POMPE","MUCOPOLISACARIDOSIS TIPO I",
"MUCOPOLISACARIDOSIS TIPO II","MUCOPOLISACARIDOSIS TIPO VI","ENFERMEDADES POCO FRECUENTES","ATROFIA MUSCULAR ESPINAL",
"TIROSINEMIA TIPO I","HEMOGLOBINURIA PAROXÍSTICA NOCTURNA","SÍNDROME URÉMICO HEMOLÍTICO ATÍPICO",
"ENFERMEDAD FIBROQUÍSTICA DEL PÁNCREAS","HIPERTENSIÓN ARTERIAL PULMONAR (HAP)","ESCLEROSIS MÚLTIPLE",
"DÉFICIT DE HORMONA DE CRECIMIENTO","TRASPLANTE DE ÓRGANOS Y PRECURSORES HEMATOPOYÉTICOS","INMUNOSUPRESIÓN POST TRASPLANTE",
"INFECCIÓN POR VIRUS DE LA INMUNODEFICIENCIA HUMANA (HIV)","HEPATITIS CRÓNICA POR VIRUS C",
"ANEURISMA DE AORTA ABDOMINAL / ANEURISMA DE AORTA TORÁCICA",
"PROCESOS ARTERIALES: OBSTRUCTIVOS, ESTENÓTICOS, ANEURISMÁTICOS, DEFORMATIVOS, CONGÉNITOS","ESTENOSIS VALVULAR AÓRTICA",
"INSUFICIENCIA CARDÍACA AGUDA / SHOCK CARDIOGÉNICO","INSUFICIENCIA CARDÍACA - INSUFICIENCIA RESPIRATORIA",
"ARRITMIAS VENTRICULARES. PREVENCIÓN DE MUERTE SÚBITA CARDÍACA","ENFERMEDAD DE PARKINSON REFRACTARIA AL TRATAMIENTO",
"DOLOR CRÓNICO INTRATABLE","EPILEPSIA REFRACTARIA AL TRATAMIENTO MÉDICO","AMPUTACIÓN DE MIEMBRO INFERIOR O SUPERIOR",
"PRÓTESIS DE IMPLANTE TRAUMATOLÓGICAS","HIPOACUSIA DE DIFERENTES ORÍGENES","FERTILIDAD","DROGODEPENDENCIA",
"DIABETES MELLITUS","HEMOFILIA A Y HEMOFILIA B",
"PACIENTES CON INTERNACIÓN EN INSTITUCIONES DE REHABILITACIÓN DE ALTA COMPLEJIDAD (TERCER NIVEL)",
"MÓDULO DE PROFILAXIS PREEXPOSICIÓN (PREP):"]
TITLE_NK = {nk(t): t for t in TITLES}
# encabezados de especialidad (agrupan patologías; tienen texto común)
ESPEC = {nk(t) for t in ["ONCOLOGÍA","ONCOHEMATOLOGÍA","REUMATOLOGÍA","ENFERMEDAD INFLAMATORIA INTESTINAL",
    "ENFERMEDADES LISOSOMALES","ENFERMEDADES POCO FRECUENTES","TRASPLANTE DE ÓRGANOS Y PRECURSORES HEMATOPOYÉTICOS"]}

pdf = pdfplumber.open(PDF)
lines = []
for pi in range(2, len(pdf.pages)):                      # 0-1 = portada + índice
    for ln in (pdf.pages[pi].extract_text() or '').split('\n'):
        s = ln.rstrip()
        if re.fullmatch(r'\s*\d{1,3}\s*', s): continue    # nº de página suelto
        if s.strip(): lines.append(s.strip())

# detectar comienzos de sección (título en 1 o 2 líneas). Cada título arranca UNA
# sección: su 1ª aparición. Reapariciones (p.ej. listados de radioterapia) son contenido.
marks = []; seen_title = set()
i = 0
while i < len(lines):
    one = nk(lines[i])
    two = nk(lines[i] + ' ' + lines[i+1]) if i+1 < len(lines) else ''
    if two in TITLE_NK and two not in seen_title:
        marks.append((i, i+2, TITLE_NK[two])); seen_title.add(two); i += 2; continue
    if one in TITLE_NK and one not in seen_title:
        marks.append((i, i+1, TITLE_NK[one])); seen_title.add(one); i += 1; continue
    i += 1

# ---------- 3) estructurar cada sección en bloques ----------
LABELS = ["tecnología","tecnologia","fundamento terapéutico","fundamento terapeutico",
 "fundamentos terapéuticos","fundamento","información requerida","informacion requerida",
 "empadronamiento del beneficiario","empadronamiento","actualización semestral","actualizacion semestral",
 "documentación respaldatoria","documentacion respaldatoria","prestaciones incluidas","prestaciones",
 "prótesis incluida","protesis incluida","prótesis incluidas","observaciones","observación","observacion",
 "esquema terapéutico","esquemas terapéuticos","información requerida para la actualización","seguimiento"]
def is_label(s):
    sl = s.lower().rstrip(':').strip()
    if s.endswith(':') and len(s) <= 65 and len(s.split()) <= 7 and not re.match(r'^\d', s):
        return True
    if sl in LABELS: return True
    if re.match(r'^[A-ZÁÉÍÓÚ]{4,}:?$', s) and len(s.split()) <= 3:   # PRELINGUALES: / POSTLINGUALES:
        return True
    return False
def is_sub(s):   return bool(re.match(r'^[A-Z]\.\s+\S', s) or re.match(r'^[a-z]\)\s+\S', s))
def is_item(s):  return bool(re.match(r'^\d{1,2}[\.\-\)]\s+\S', s) or re.match(r'^[•▪◦·]\s*\S', s) or re.match(r'^o\s+[A-ZÁÉÍÓÚ]', s))

def structure(seg):
    bloques = []
    for raw in seg:
        s = raw.strip()
        if not s: continue
        if is_sub(s):      bloques.append({"t":"sub","x":s}); continue
        if is_label(s):    bloques.append({"t":"label","x":s.rstrip(':')}); continue
        if is_item(s):     bloques.append({"t":"li","x":re.sub(r'^(\d{1,2}[\.\-\)]|[•▪◦·]|o)\s*','',s)}); continue
        # continuación de línea sólo si arranca en minúscula o el anterior corta con guión;
        # una línea nueva en mayúscula es un párrafo/encabezado nuevo (no se fusiona).
        if bloques and bloques[-1]["t"] in ("li","p") and (bloques[-1]["x"].endswith('-') or (s[0].islower() or s[0] in '(¿"')):
            prev = bloques[-1]["x"]
            bloques[-1]["x"] = prev[:-1]+s if prev.endswith('-') else prev+' '+s
        else:
            bloques.append({"t":"p","x":s})
    # limpiar guiones de corte
    for b in bloques: b["x"] = re.sub(r'\s+',' ',b["x"]).strip()
    return bloques

def req_from_bloques(bloques):
    """extrae la lista 'Información requerida' (todos los ítems bajo esa etiqueta)."""
    out, capting = [], False
    for b in bloques:
        if b["t"] == "label":
            capting = "informaci" in nk(b["x"]).lower() or "INFORMACIONREQUERIDA" in nk(b["x"])
            continue
        if b["t"] == "sub":  # un sub-módulo no corta la captura si vuelve a aparecer la etiqueta
            continue
        if capting and b["t"] == "li":
            out.append(b["x"])
        elif capting and b["t"] == "p":
            capting = False
    # dedup preservando orden
    seen=set(); ded=[]
    for x in out:
        k=nk(x)
        if k not in seen: seen.add(k); ded.append(x)
    return ded

sections = []
for idx,(a,b,title) in enumerate(marks):
    end = marks[idx+1][0] if idx+1 < len(marks) else len(lines)
    seg = lines[b:end]
    bloques = structure(seg)
    sections.append({"title": title, "nk": nk(title), "es_especialidad": nk(title) in ESPEC,
                     "bloques": bloques, "requerimiento_pdf": req_from_bloques(bloques),
                     "raw": ' '.join(seg)})

# especialidad de cada patología: membresía explícita a un grupo; el resto es
# patología independiente (especialidad = su propio nombre).
GROUPS = {
 "ONCOLOGÍA":["CÁNCER DE MAMA","CÁNCER DE COLON","CÁNCER DE PRÓSTATA","CÁNCER DE PULMÓN","CÁNCER DE RIÑÓN",
   "MELANOMA","MÓDULO DE RADIOTERAPIA ONCOLÓGICA"],
 "ONCOHEMATOLOGÍA":["MIELOMA MÚLTIPLE","LEUCEMIA MIELOIDE CRÓNICA (LMC)"],
 "REUMATOLOGÍA":["ARTRITIS REUMATOIDEA","ARTRITIS PSORIÁSICA","PSORIASIS EN PLACA",
   "ARTRITIS IDIOPÁTICA JUVENIL SISTÉMICA (AIJS)","ESPONDILITIS ANQUILOSANTE-ESPONDILITIS AXIAL NO RADIOGRÁFICA"],
 "ENFERMEDAD INFLAMATORIA INTESTINAL":["ENFERMEDAD DE CROHN","COLITIS ULCEROSA"],
 "ENFERMEDADES LISOSOMALES":["ENFERMEDAD DE FABRY (EF)","ENFERMEDAD DE GAUCHER (EG)","ENFERMEDAD DE POMPE",
   "MUCOPOLISACARIDOSIS TIPO I","MUCOPOLISACARIDOSIS TIPO II","MUCOPOLISACARIDOSIS TIPO VI"],
 "ENFERMEDADES POCO FRECUENTES":["ATROFIA MUSCULAR ESPINAL","TIROSINEMIA TIPO I","HEMOGLOBINURIA PAROXÍSTICA NOCTURNA",
   "SÍNDROME URÉMICO HEMOLÍTICO ATÍPICO"],
 "TRASPLANTE DE ÓRGANOS Y PRECURSORES HEMATOPOYÉTICOS":["INMUNOSUPRESIÓN POST TRASPLANTE"],
}
MEMBER_OF = {}
for g, mem in GROUPS.items():
    for m in mem: MEMBER_OF[nk(m)] = g
for sec in sections:
    sec["especialidad"] = MEMBER_OF.get(sec["nk"], sec["title"])

# ---------- 4) IDs, CIE y cruce de códigos ----------
def slug(t):
    return re.sub(r'[^a-z0-9]+','_', unicodedata.normalize('NFD',t).encode('ascii','ignore').decode().lower()).strip('_')[:34]
for sec in sections: sec["id"] = slug(sec["title"])

# CIE-10 por palabra clave del título (orientativo)
CIE_KW = [("CANCERDEMAMA",["C50"]),("CANCERDECOLON",["C18","C19","C20"]),("CANCERDEPROSTATA",["C61"]),
 ("CANCERDEPULMON",["C34"]),("CANCERDERINON",["C64"]),("MELANOMA",["C43"]),("MIELOMA",["C90"]),
 ("LEUCEMIAMIELOIDE",["C92.1"]),("ARTRITISREUMATOIDEA",["M05","M06"]),("ARTRITISPSORIASICA",["L40.5","M07"]),
 ("PSORIASIS",["L40"]),("ARTRITISIDIOPATICAJUVENIL",["M08"]),("ESPONDILITIS",["M45","M46"]),
 ("ENFERMEDADDECROHN",["K50"]),("COLITISULCEROSA",["K51"]),("FABRY",["E75.2"]),("GAUCHER",["E75.2"]),
 ("POMPE",["E74.0"]),("MUCOPOLISACARIDOSISTIPOI",["E76.0","E76.1"]),("MUCOPOLISACARIDOSISTIPOII",["E76.1"]),
 ("MUCOPOLISACARIDOSISTIPOVI",["E76.2"]),("ATROFIAMUSCULAR",["G12.0","G12.1"]),("TIROSINEMIA",["E70.2"]),
 ("HEMOGLOBINURIA",["D59.5"]),("UREMICOHEMOLITICO",["D59.3"]),("FIBROQUISTICA",["E84"]),
 ("HIPERTENSIONARTERIALPULMONAR",["I27.0","I27.2"]),("ESCLEROSISMULTIPLE",["G35"]),("HORMONADECRECIMIENTO",["E23.0"]),
 ("INMUNODEFICIENCIAHUMANA",["B20","B24","Z21"]),("HEPATITISCRONICAPORVIRUSC",["B18.2"]),
 ("ANEURISMADEAORTA",["I71"]),("PROCESOSARTERIALES",["I70","I72","I77"]),("ESTENOSISVALVULARAORTICA",["I35.0"]),
 ("INSUFICIENCIACARDIACAAGUDA",["I50.1","R57.0"]),("INSUFICIENCIACARDIACAINSUFICIENCIARESPIRATORIA",["I50","J96"]),
 ("ARRITMIASVENTRICULARES",["I47.2","I49"]),("PARKINSON",["G20"]),("DOLORCRONICO",["G89.2","R52.1"]),
 ("EPILEPSIA",["G40"]),("AMPUTACIONDEMIEMBRO",["Z89"]),("PROTESISDEIMPLANTETRAUMATOLOGICAS",["Z96.6"]),
 ("HIPOACUSIA",["H90","H91"]),("FERTILIDAD",["N46","N97"]),("DROGODEPENDENCIA",["F19"]),
 ("DIABETESMELLITUS",["E10","E11"]),("HEMOFILIA",["D66","D67"]),("INMUNOSUPRESIONPOSTTRASPLANTE",["Z94"]),
 ("TRASPLANTEDEORGANOS",["Z94"]),("REHABILITACION",["Z50"]),("PROFILAXISPREEXPOSICION",["Z20.6"]),
 ("RADIOTERAPIA",["Z51.0"])]
def cie_for(k):
    for kw,cie in CIE_KW:
        if kw in k: return cie
    return []
for sec in sections: sec["cie"] = cie_for(sec["nk"])

# medicación + requerimiento VISITAR (Excel) por prefijo/inclusión de clave
def excel_for(k):
    med, reqv = [], []
    for ek,ev in excel.items():
        core = k.replace("HAP","").replace("SINTOMATICO","")
        if ek.startswith(core) or core in ek or ("HEMOFILIA" in k and ek.startswith("HEMOFILIA")):
            for m in ev["medicacion"]:
                if m not in med: med.append(m)
            for q in ev["requerimiento_visitar"]:
                if q not in reqv: reqv.append(q)
    return med, reqv
for sec in sections:
    med, reqv = excel_for(sec["nk"])
    sec["medicacion"] = med
    sec["requerimiento_visitar"] = reqv

# códigos (SUR)/(SURGE) -> sección, por palabra clave de la práctica
CODE_MAP = {
 "40010218":"parkinson","40010219":"dolor_cronico","40010220":"epilepsia","40010221":"epilepsia",
 "40010708":"procesos_arteriales","40010709":"procesos_arteriales","40010710":"procesos_arteriales","40070806":"procesos_arteriales",
 "40030220":"hipoacusia","40318105":"hipoacusia",
 "40050401":"trasplante_organos","40288401":"trasplante_organos","40288402":"trasplante_organos",
 "40070115":"arritmias","40070203":"estenosis_valvular","40070208":"aneurisma_aorta",
 "40070901":"trasplante_organos","40070902":"trasplante_organos","40070903":"trasplante_organos","40070904":"trasplante_organos",
 "40081001":"trasplante_organos","40081002":"trasplante_organos","40081003":"trasplante_organos","40081005":"trasplante_organos",
 "40201001":"trasplante_organos","40209090":"trasplante_organos","40209091":"trasplante_organos","40209092":"trasplante_organos",
 "40230234":"trasplante_organos","40241202":"trasplante_organos","40241203":"trasplante_organos",
 "40270201":"trasplante_organos","40270202":"trasplante_organos",
 "40350115":"radioterapia","40350120":"radioterapia",
 "40380301":"insuf_respiratoria","665922":"hepatitis_c","665948":"hepatitis_c",
}
# resolver alias -> id real de sección por palabra clave
ALIAS = {"parkinson":"PARKINSON","dolor_cronico":"DOLORCRONICO","epilepsia":"EPILEPSIA",
 "procesos_arteriales":"PROCESOSARTERIALES","hipoacusia":"HIPOACUSIA","trasplante_organos":"TRASPLANTEDEORGANOS",
 "arritmias":"ARRITMIASVENTRICULARES","estenosis_valvular":"ESTENOSISVALVULARAORTICA","aneurisma_aorta":"ANEURISMADEAORTA",
 "radioterapia":"RADIOTERAPIA","insuf_respiratoria":"INSUFICIENCIACARDIACAINSUFICIENCIARESPIRATORIA","hepatitis_c":"HEPATITISCRONICAPORVIRUSC"}
sec_by_kw = {}
for sec in sections:
    for al,kw in ALIAS.items():
        if kw in sec["nk"] and al not in sec_by_kw:
            sec_by_kw[al] = sec["id"]
codigo_patologia = {}
for code, alias in CODE_MAP.items():
    sid = sec_by_kw.get(alias)
    if sid: codigo_patologia[code] = sid
# adjuntar códigos a cada sección
for sec in sections: sec["codigos"] = []
for code, sid in codigo_patologia.items():
    s = next((x for x in sections if x["id"] == sid), None)
    if s and code not in s["codigos"]: s["codigos"].append(code)

# requerimiento final = el del Excel (lo que pide VISITAR) si existe, si no el del PDF
for sec in sections:
    sec["requerimiento"] = sec["requerimiento_visitar"] or sec["requerimiento_pdf"]
    sec["_h_extra"] = ""

out = {
 "resolucion":"Resolución 731/2023 (Anexo II) — Sistema Único de Reintegro por Gestión de Enfermedades (SURGE)",
 "nota":"Reintegro por gestión de enfermedades. «Requerimiento VISITAR» es lo que VISITAR solicita al afiliado para autorizar; el detalle del PDF (fundamento, información requerida, prestaciones, observaciones) es el texto oficial del Anexo II.",
 "especialidades": [],
 "patologias": [],
 "codigo_patologia": codigo_patologia,
}
esp_order = []
for sec in sections:
    if sec["es_especialidad"] and not sec["bloques"] and not sec["codigos"]:
        pass  # encabezado vacío: se omite como patología, pero define especialidad
    e = sec["especialidad"]
    if e not in esp_order: esp_order.append(e)
    out["patologias"].append({
        "id": sec["id"], "nombre": sec["title"], "especialidad": sec["especialidad"],
        "es_especialidad": sec["es_especialidad"],
        "medicacion": sec["medicacion"], "requerimiento": sec["requerimiento"],
        "requerimiento_pdf": sec["requerimiento_pdf"],
        "bloques": sec["bloques"], "cie": sec["cie"], "codigos": sec["codigos"],
    })
out["especialidades"] = esp_order

json.dump(out, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
nb = sum(len(p["bloques"]) for p in out["patologias"])
print(f"SURGE: secciones {len(out['patologias'])} · bloques {nb} · con medicación {sum(1 for p in out['patologias'] if p['medicacion'])} · con requerimiento {sum(1 for p in out['patologias'] if p['requerimiento'])} · códigos cruzados {len(codigo_patologia)}/38", file=sys.stderr)
