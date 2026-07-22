#!/usr/bin/env python3
"""SURGE — Sistema Único de Reintegro por Gestión de Enfermedades (Res. 731/2023, Anexo II).
Cruza:
  - patologías (del Excel: medicación SURGE + requerimiento de autorización VISITAR),
  - patologías por procedimiento/módulo (del PDF Anexo II),
  - códigos del nomenclador marcados (SUR)/(SURGE),
  - diagnósticos CIE-10 relacionados.
Genera data/surge.json."""
import json, re, sys, zipfile
import xml.etree.ElementTree as ET

ODS = sys.argv[1] if len(sys.argv) > 1 else "data/surge.ods"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/surge.json"

# ---------- 1) leer el Excel (patologías por droga) ----------
T = '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
def read_ods(path):
    z = zipfile.ZipFile(path); root = ET.fromstring(z.read('content.xml'))
    table = next(root.iter(T+'table'))
    rows = []
    for r in table.iter(T+'table-row'):
        vals = []
        for c in r.findall(T+'table-cell'):
            rep = int(c.get(T+'number-columns-repeated','1'))
            txt = ''.join(t for t in c.itertext())
            vals.extend([txt]*min(rep,10))
        while vals and vals[-1] == '': vals.pop()
        rows.append(vals)
    return rows

def split_items(s):
    if not s: return []
    s = re.sub(r'\s+',' ',s.replace('\n',' ')).strip()
    s = re.sub(r'^[-*]\s*','',s)                     # quita viñeta inicial
    # separa en "- "/"* " sólo cuando sigue una MAYÚSCULA (evita "TDMI - 1")
    parts = re.split(r'\s*[-*]\s+(?=[A-ZÁÉÍÓÚÑ])', s)
    out = []
    for p in parts:
        p = re.sub(r'\s+',' ',p).strip(' -*.,')
        if len(p) >= 2: out.append(p)
    return out

def nk(s):                                          # clave normalizada (sin espacios/acentos)
    s = s.upper()
    for a,b in [('Á','A'),('É','E'),('Í','I'),('Ó','O'),('Ú','U'),('Ü','U'),('Ñ','N')]:
        s = s.replace(a,b)
    return re.sub(r'[^A-Z0-9]','',s)

excel = {}
try:
    for r in read_ods(ODS):
        if len(r) >= 2 and r[0] and nk(r[0]) not in ('PATOLOGIA',) and 'SISTEMAUNICO' not in nk(r[0]):
            meds = split_items(r[1] if len(r) > 1 else '')
            reqs = split_items(r[2] if len(r) > 2 else '')
            excel[nk(r[0])] = {"medicacion": meds, "requerimiento": reqs}
except FileNotFoundError:
    print("aviso: no se encontró el Excel SURGE", file=sys.stderr)

# ---------- 2) catálogo canónico de patologías (Anexo II del PDF) ----------
# cada entrada: (id, nombre, especialidad, [claves excel], [CIE-10], [reqs propios si no hay excel])
CANON = [
 # ---- ONCOLOGÍA ----
 ("ca_mama","Cáncer de mama","Oncología",["CANCERDEMAMAAVANZADO","CANCERDEMAMAADYUVANCIA"],["C50"],[]),
 ("ca_colon","Cáncer de colon","Oncología",["CANCERDECOLON"],["C18","C19","C20"],[]),
 ("ca_prostata","Cáncer de próstata","Oncología",["CANCERDEPROSTATA"],["C61"],[]),
 ("ca_pulmon","Cáncer de pulmón","Oncología",["CANCERDEPULMON"],["C34"],[]),
 ("ca_rinon","Cáncer de riñón","Oncología",["CANCERDERINON"],["C64"],[]),
 ("melanoma","Melanoma","Oncología",["MELANOMA"],["C43"],[]),
 ("radioterapia","Módulo de radioterapia oncológica","Oncología",[],["Z51.0"],
   ["RHC","Informe de anatomía patológica","Estadificación","Plan de tratamiento radiante"]),
 # ---- ONCOHEMATOLOGÍA ----
 ("mieloma","Mieloma múltiple","Oncohematología",["MIELOMAMULTIPLE"],["C90"],[]),
 ("lmc","Leucemia mieloide crónica (LMC)","Oncohematología",["LEUCEMIAMIELOIDECRONICALMC"],["C92.1"],[]),
 # ---- REUMATOLOGÍA ----
 ("ar","Artritis reumatoidea","Reumatología",["ARTRITISREUMATOIDEA"],["M05","M06"],[]),
 ("aps","Artritis psoriásica","Reumatología",["ARTRITISPSORIASICA"],["L40.5","M07"],[]),
 ("psoriasis","Psoriasis en placa","Reumatología",["PSORIASISENPLACA"],["L40"],[]),
 ("aij","Artritis idiopática juvenil","Reumatología",["ARTRITISIDIOPATICAJUVENIL"],["M08"],[]),
 ("espondilitis","Espondilitis anquilosante / axial","Reumatología",["ESPONDILITIS"],["M45","M46"],[]),
 # ---- ENFERMEDAD INFLAMATORIA INTESTINAL ----
 ("crohn","Enfermedad de Crohn","Enfermedad inflamatoria intestinal",["ENFERMEDADDECROHN"],["K50"],[]),
 ("colitis","Colitis ulcerosa","Enfermedad inflamatoria intestinal",["COLITISULCEROSA"],["K51"],[]),
 # ---- ENFERMEDADES LISOSOMALES ----
 ("fabry","Enfermedad de Fabry","Enfermedades lisosomales",["ENFERMEDADDEFABRY"],["E75.2"],[]),
 ("gaucher","Enfermedad de Gaucher","Enfermedades lisosomales",["ENFERMEDADDEGAUCHER"],["E75.2"],[]),
 ("pompe","Enfermedad de Pompe","Enfermedades lisosomales",["ENFERMEDADDEPOMPE"],["E74.0"],[]),
 ("mps1","Mucopolisacaridosis tipo I","Enfermedades lisosomales",["MULTIPOLISACARIDOSISTIPOI"],["E76.0","E76.1"],[]),
 ("mps2","Mucopolisacaridosis tipo II","Enfermedades lisosomales",["MULTIPOLISACARIDOSISTIPOII"],["E76.1"],[]),
 ("mps6","Mucopolisacaridosis tipo VI","Enfermedades lisosomales",["MULTIPOLISACARIDOSISTIPOVI"],["E76.2"],[]),
 # ---- ENFERMEDADES POCO FRECUENTES ----
 ("ame","Atrofia muscular espinal (AME)","Enfermedades poco frecuentes",["ATROFIAMUSCULARESPINALAME"],["G12.0","G12.1"],[]),
 ("tirosinemia","Tirosinemia tipo I","Enfermedades poco frecuentes",["TIROSINEMIATIPOI"],["E70.2"],[]),
 ("hpn","Hemoglobinuria paroxística nocturna","Enfermedades poco frecuentes",["HEMOGLOBINURIAPAROXISTICANOCTURNA"],["D59.5"],[]),
 ("suha","Síndrome urémico hemolítico atípico (SUHa)","Enfermedades poco frecuentes",["SINDROMEUREMICOHEMOLITICOATIPICOSUHA"],["D59.3"],[]),
 # ---- OTRAS PATOLOGÍAS POR DROGA ----
 ("fq","Enfermedad fibroquística del páncreas","Enfermedad fibroquística del páncreas",
   ["ENFERMEDADFIBROQUISTICADELPANCREASSINTOMATICO","ENFERMEDADFIBROQUISTICADELPANCREASMODULADORES"],["E84"],[]),
 ("hap","Hipertensión arterial pulmonar (HAP)","Hipertensión arterial pulmonar",
   ["HIPERTENSIONARTERIALPULMONARTRATAMIENTOCON1DROGA","HIPERTENSIONARTERIALPULMONARTRATAMIENTOCON2DROGA"],["I27.0","I27.2"],[]),
 ("em","Esclerosis múltiple","Esclerosis múltiple",["ESCLEROSISMULTIPILE"],["G35"],[]),
 ("ghd","Déficit de hormona de crecimiento","Déficit de hormona de crecimiento",["DEFICITDEHORMONASDECRECIMIENTO"],["E23.0"],[]),
 ("inmunosupresion","Inmunosupresión post trasplante","Trasplante de órganos y precursores hematopoyéticos",
   ["INMUNOSUPRESIONPOSTTRASPLANTE"],["Z94"],[]),
 ("hiv","Infección por HIV","HIV",["HIV"],["B20","B24","Z21"],[]),
 ("hepc","Hepatitis crónica por virus C","Hepatitis crónica por virus C",["HEPATITISC"],["B18.2"],[]),
 ("prep","Módulo de profilaxis preexposición (PrEP)","Profilaxis preexposición",["PROFILAXISPREEXPOSICIONPREP"],["Z20.6"],[]),
 ("diabetes","Diabetes mellitus","Diabetes mellitus",[],["E10","E11"],
   ["RHC","Laboratorio (HbA1c, glucemia)","Esquema terapéutico","Tratamientos previos"]),
 ("drogodependencia","Drogodependencia","Drogodependencia",[],["F19"],
   ["RHC","Evaluación por salud mental","Plan de tratamiento"]),
 ("fertilidad","Fertilidad","Fertilidad",[],["N46","N97"],
   ["RHC","Estudios de fertilidad de ambos miembros","Tratamientos previos"]),
 # ---- HEMOFILIA ----
 ("hemofilia_a","Hemofilia A","Hemofilia",
   ["HEMOFILIAAPROFILAXIS","HEMOFILIAADEMANDAOPROFILAXISINTERMITENTE","HEMOFILIAAINMUNOTOLERANCIA"],["D66"],[]),
 ("hemofilia_b","Hemofilia B","Hemofilia",
   ["HEMOFILIABPROFILAXIS","HEMOFILIABDEMANDAOPROFILAXISINTERMITENTE"],["D67"],[]),
 # ---- PATOLOGÍAS POR PROCEDIMIENTO / MÓDULO (códigos del nomenclador) ----
 ("parkinson","Enfermedad de Parkinson refractaria al tratamiento","Neurología",[],["G20"],
   ["RHC","Escala UPDRS","Respuesta a levodopa","Tratamientos previos"]),
 ("dolor_cronico","Dolor crónico intratable","Neurología",[],["G89.2","R52.1"],
   ["RHC","Escala de dolor","Tratamientos previos","Evaluación multidisciplinaria"]),
 ("epilepsia","Epilepsia refractaria al tratamiento médico","Neurología",[],["G40"],
   ["RHC","Video-EEG","RMN de cerebro","Fármacos antiepilépticos utilizados","Tratamientos previos"]),
 ("procesos_arteriales","Procesos arteriales y aneurismas craneales","Cirugía vascular / Neurocirugía",[],["I67.1","I72"],
   ["RHC","Angiografía / Angio-TC","Informe de imagen","Tratamientos previos"]),
 ("aneurisma_aorta","Aneurisma de aorta abdominal / torácica","Cirugía vascular",[],["I71"],
   ["RHC","Angio-TC de aorta","Diámetro del aneurisma","Tratamientos previos"]),
 ("estenosis_aortica","Estenosis valvular aórtica (TAVI)","Cardiología",[],["I35.0"],
   ["RHC","Ecocardiograma Doppler","Área valvular / gradiente","Score de riesgo quirúrgico","Tratamientos previos"]),
 ("arritmias","Arritmias ventriculares — prevención de muerte súbita","Cardiología",[],["I47.2","I49"],
   ["RHC","ECG / Holter","Fracción de eyección","Estudio electrofisiológico","Tratamientos previos"]),
 ("insuf_cardiaca","Insuficiencia cardíaca aguda / insuficiencia respiratoria (ECMO)","Cardiología / Terapia intensiva",[],["I50","J96"],
   ["RHC","Parámetros hemodinámicos","Indicación de ECMO","Tratamientos previos"]),
 ("hipoacusia","Hipoacusia — implante coclear","Otorrinolaringología",[],["H90","H91"],
   ["RHC","Audiometría","Potenciales evocados auditivos","Evaluación fonoaudiológica","Tratamientos previos"]),
 ("tx_cardiaco","Trasplante cardíaco","Trasplante de órganos y precursores hematopoyéticos",[],["Z94.1"],
   ["RHC","Protocolo de trasplante","Estudios pretrasplante","Dictamen del INCUCAI"]),
 ("tx_pulmon","Trasplante de pulmón","Trasplante de órganos y precursores hematopoyéticos",[],["Z94.2"],
   ["RHC","Protocolo de trasplante","Estudios pretrasplante","Dictamen del INCUCAI"]),
 ("tx_hepatico","Trasplante hepático","Trasplante de órganos y precursores hematopoyéticos",[],["Z94.4"],
   ["RHC","Protocolo de trasplante","Estudios pretrasplante","Dictamen del INCUCAI"]),
 ("tx_renal","Trasplante renal","Trasplante de órganos y precursores hematopoyéticos",[],["Z94.0"],
   ["RHC","Protocolo de trasplante","Estudios pretrasplante","Dictamen del INCUCAI"]),
 ("tx_medula","Trasplante de médula ósea / precursores hematopoyéticos","Trasplante de órganos y precursores hematopoyéticos",[],["Z94.8"],
   ["RHC","Indicación de trasplante","Estudios pretrasplante","Tipificación HLA","Tratamientos previos"]),
 ("hepatitis_lab","Hepatitis — carga viral (estudios SURGE)","Hepatitis crónica por virus C",[],["B18"],
   ["RHC","Genotipo","Estadio de fibrosis","Carga viral"]),
]

# ---------- 3) mapeo de códigos (SUR)/(SURGE) -> patología ----------
CODE_MAP = {
 "40010218":"parkinson","40010219":"dolor_cronico","40010220":"epilepsia","40010221":"epilepsia",
 "40010708":"procesos_arteriales","40010709":"procesos_arteriales","40010710":"procesos_arteriales","40070806":"procesos_arteriales",
 "40030220":"hipoacusia","40318105":"hipoacusia",
 "40050401":"tx_pulmon","40288401":"tx_pulmon","40288402":"tx_pulmon",
 "40070115":"arritmias","40070203":"estenosis_aortica","40070208":"aneurisma_aorta",
 "40070901":"tx_cardiaco","40070902":"tx_cardiaco","40070903":"tx_cardiaco","40070904":"tx_cardiaco",
 "40081001":"tx_hepatico","40081002":"tx_hepatico","40081003":"tx_hepatico","40081005":"tx_hepatico",
 "40201001":"tx_hepatico","40209090":"tx_hepatico","40209091":"tx_hepatico","40209092":"tx_hepatico",
 "40230234":"tx_medula","40241202":"tx_medula","40241203":"tx_medula",
 "40270201":"tx_renal","40270202":"tx_renal",
 "40350115":"radioterapia","40350120":"radioterapia",
 "40380301":"insuf_cardiaca",
 "665922":"hepatitis_lab","665948":"hepatitis_lab",
}

# ---------- 4) armar la salida ----------
by_id = {}
esp_order = []
for pid, nombre, esp, exkeys, cie, reqs_own in CANON:
    meds, reqs = [], list(reqs_own)
    for kk in exkeys if False else exkeys:  # merge de todas las variantes del excel
        pass
    for kk in exkeys:
        e = excel.get(kk)
        if e:
            for m in e["medicacion"]:
                if m not in meds: meds.append(m)
            for q in e["requerimiento"]:
                if q not in reqs: reqs.append(q)
    by_id[pid] = {"id":pid,"nombre":nombre,"especialidad":esp,
                  "medicacion":meds,"requerimiento":reqs,"cie":cie,"codigos":[]}
    if esp not in esp_order: esp_order.append(esp)

# adjuntar códigos
for code, pid in CODE_MAP.items():
    if pid in by_id and code not in by_id[pid]["codigos"]:
        by_id[pid]["codigos"].append(code)

# aviso de claves del excel no usadas
used = set()
for _,_,_,exkeys,_,_ in CANON: used.update(exkeys)
missing = [k for k in excel if k not in used]
if missing:
    print("excel sin mapear:", missing, file=sys.stderr)

out = {
 "resolucion":"Resolución 731/2023 (Anexo II) — Sistema Único de Reintegro por Gestión de Enfermedades (SURGE)",
 "nota":"Reintegro por gestión de enfermedades. La columna «Requerimiento» detalla lo que VISITAR solicita al afiliado para autorizar la cobertura.",
 "especialidades": esp_order,
 "patologias": list(by_id.values()),
 "codigo_patologia": CODE_MAP,
}
json.dump(out, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
nmed = sum(1 for p in out["patologias"] if p["medicacion"])
print(f"SURGE: patologías {len(out['patologias'])} · con medicación {nmed} · códigos cruzados {len(CODE_MAP)} · especialidades {len(esp_order)}", file=sys.stderr)
