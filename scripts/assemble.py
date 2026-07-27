#!/usr/bin/env python3
"""Assemble the unified intelligent NBU database from catalog.json + intel.json (+ 2024 overlay)."""
import json, re, sys, unicodedata
from collections import defaultdict

catalog = json.load(open("catalog.json"))
intel = json.load(open("intel.json"))
SIN = intel["sinonimias"]; ABBR = intel["abreviaturas"]; NORMAS = intel["normas"]

def norm(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return s

# ---------- grupo (especialidad) classifier — orientativo ----------
# ordered (first match wins); patterns matched against normalized name+synonyms
GRUPOS = [
    ("Gestión administrativa", r"acto bioquimico administrativo|validacion|auditoria|autorizacion de la orden"),
    ("Marcadores tumorales", r"\bpsa\b|antigeno prostatico|\bcea\b|ca 125|ca 15|ca 19|ca 72|ca 21|cyfra|marcador tumoral|alfa feto|\bafp\b|beta 2 microglob|cromogranina|her 2|\bnse\b|\bscc\b|\bhe4\b|s-100|tiroglobulina"),
    ("Endocrinología y hormonas", r"\btsh\b|tiroxina|\bt3\b|\bt4\b|tirotrofina|triiodo|cortisol|\bacth\b|\bfsh\b|\blh\b|prolactina|testosterona|estradiol|estriol|estrona|progesterona|\binsulina\b|\bpth\b|parathormona|hormona|aldosterona|dhea|androst|renina|angiotensina|calcitonina|somato|gastrina|antimulleriana|17-ho|vitamina d|peptido c|glucagon|\bhcg\b|gonadotrofina|catecolamina|metanefrina|serotonina|vainillin|homovanilic|adiuretica|vasopresina"),
    ("Serología infecciosa y virología", r"hiv|hepatitis|chagas|toxoplasmosis|rubeola|citomegalo|\bcmv\b|epstein|dengue|\bvdrl\b|herpes|\bhpv\b|\bvph\b|brucel|hidatidosis|sifilis|\bftaabs\b|mononucleosis|widal|\btorch\b|sarampion|parvovirus|treponema|leptospira|bordetella|chlamydia|mycoplasma|ureaplasma|\bvirus\b|\bveb\b|\bvz\b|varicela|coxsackie|echovirus|echo |adenovirus|influenza|zika|chikungunya|west nile|htlv|paperas|parotiditis|streptococc|salmonella|rickettsia|coxiella|bartonella|borrelia|coccidioides|aspergill|candida|cryptococ|echinococc|trichin|toxocara|strongyloides|helicobacter|bordet|hantavirus|rotavirus|norovirus|sincicial|blastomyces|histoplasma|paracoccidio|acanthamoeba"),
    ("Microbiología y parasitología", r"cultivo|antibiograma|baciloscopia|coprocultivo|urocultivo|hemocultivo|exudado|bacteriolog|\bgram\b|micolog|parasit|coproparasit|directo y cultivo|germen|antibiotic|micogram|antimicog|clostridium|leishmania|paludismo|malaria|graham|mantoux|\bppd\b|multirresist|carbapenem|mycobacterium|anaerobios|colonias|campylobacter|cholerae|bacilus|antigenos bacterianos|corpusculos"),
    ("Autoinmunidad e inmunología", r"anticuerpo|ac\. anti|ac\. igg|ac\. igm|ac\. iga|\banti-|\bana\b|\bfan\b|\baan\b|complemento|inmunoglobulina|\biga\b|\bigg\b|\bigm\b|\bige\b|\bigd\b|\banca\b|factor reumatoid|antinuclear|antimitocondrial|antimusculo|antimembrana|endomisio|cardiolipina|glicoproteina|inmunofijacion|inmunoelectrofor|celulas le|crioglob|complejos inmunes|inmunocomplejos|\bena\b|\bacra\b|receptor|desmogleina|centromero|dna|mieloperox|acuaporina|gliadina|transglutaminasa|islote|gad|beta 2 glicop"),
    ("Genética y biología molecular", r"\bpcr\b|cariotipo|cromosoma|mutacion|secuenciacion|\bgen\b|\bfish\b|brca|\badn\b|\bdna\b|\brna\b|genotip|delec|translocacion|fragilidad|filiacion|forense|conexina|huntington|hla|hemocromatosis|factor v leiden|mthr|angelman|prader|cariotip|jak2|kras|braf|her2 |microsatelit|cadena beta|bcr"),
    ("Toxicología, drogas y monitoreo de fármacos", r"drogas de abuso|monitoreo de farmacos|\bplomo\b|mercurio|aluminio|arsenico|cadmio|cocaina|marihuana|cannabin|opiaceo|anfetamin|benzodiazep|barbituric|\balcohol\b|etanol|\blitio\b|digoxin|ciclospor|salicilat|pesticida|plaguicida|lindano|\bddt\b|\bddd\b|\bdde\b|aldrin|dieldrin|atrazina|endosulfan|organoclor|organofosfor|nitrogenado|hexacloro|tiofos|cotinina|carboxihemog|benceno|tolueno|xileno|antimonio|berilio|bromuro|talio|cianuro|codeina|desipramina|doxepina|amikacina|vancomicina|tacrolimus|metotrexato|acido valproico|fenobarbital|fenitoina|carbamazep"),
    ("Fertilidad y andrología", r"esperma|semen|espermatozoid|sims|huhner|huhner|moco cervical|capacitacion|poscoital|post-coital|fructosa|swim|matrimonial|seminal|azoosperm|androlog"),
    ("Hematología y hemostasia", r"hemograma|hematocrito|hemoglobina|\bhb\b|globulos|plaquetas|reticulocit|coagul|protrombina|fibrinogeno|factor de coagulacion|eritrosed|formula leuco|medulograma|\bvsg\b|tromboplastina|trombina|dimero|antitrombina|plasminogeno|anticoagulante lupico|\bkptt\b|frotis|hematies|heinz|falciform|crioag|grupo sanguineo|coombs|\brh\b|\brho\b|compatibilidad|factor v|cofactor|von willebrand|resistencia globular|cross match|citometria de flujo|subpoblacion linfocit|\bcd4\b|\bcd8\b|\bcd\d|natural killer|haptoglobina|meta cromatic|autohemolisis|falciformacion|leucocitaria|carbohidrato deficiente"),
    ("Errores congénitos y metabolismo", r"aminoacidos|galactosemia|biotinidasa|screening neonatal|pesquisa neonatal|fenilalanina|fenilceton|neonatal|acilcarnitina|acidos organicos|mucopolisac|acidos grasos|carnitina|lisosom|galactosidasa|glucosidasa|iduronidasa|manosidasa|chitotriosidasa|fabry|gaucher|acido metilmalonico|acido orotico|homocistein|porfirin|porfobilin|oxalico|citrico|piruvico|mucopolis|acilcarnit|guanidinacetic|cetogeno|17-oh"),
    ("Química clínica y bioquímica general", r"glucemia|glucosa|urea|creatinin|colesterol|triglicerid|transaminasa|\bgot\b|\bgpt\b|bilirrub|ionograma|calcemia|calcio|acido urico|\burico\b|fosfatasa|amilasa|lipasa|proteina|albumina|magnesio|ferremia|hierro|sodio|potasio|cloro|\bldh\b|\bcpk\b|creatinquinasa|creatinfosfo|hepatograma|lipidograma|gamma|acido base|hemoglobina glico|fructosamina|microalbumin|homa|apolipo|acido lactic|osmolar|anion gap|troponina|mioglobina|\bbnp\b|\bnt-|natriuretic|ceruloplasmina|transferrina|siderofilina|zinc|cobre|cromo|selenio|cobalto|manganeso|niquel|boro|fluor|fosfato|fosfor|vitamina|\bacido\b|acidos biliares|elastasa|calprotectina|adenosin deaminasa|colinesterasa|deshidrogenasa|dehidrogenasa|aldolasa|enzima|isoenzima"),
    ("Orina y materia fecal", r"orina completa|urinari|materia fecal|coproporfirin|sangre oculta|\bsomf\b|proteinuria|glucosuria|calculo|urocitograma|clearance|clearence|depuracion|addis|amonio|uroprotein|cuerpos reductores|melanina|acetonuria|cetonemia"),
    ("Citología y anatomía", r"papanicolaou|citolog|citometr exfol|exfoliativa|celulas neoplasic|liquido cefalorraquideo|\blcr\b|liquido de puncion|amniotico|medula osea|biopsia|puncion"),
]
GRUPO_DEFAULT = "Otros / general"

def classify(name, syns):
    hay = norm(name + " " + " ".join(syns)).replace("\n", " ")
    for grupo, pat in GRUPOS:
        if re.search(pat, hay):
            return grupo
    return GRUPO_DEFAULT

SECCION_LABEL = {
    "PMO": "PMO — Programa Médico Obligatorio",
    "PE": "Prácticas Especiales (P.E.)",
    "GESTION": "Gestión Administrativa",
}

# ---------- 2024 revalorization overlay (from the Enero-2024 anexo) ----------
def load_overlay():
    ov = {}
    try:
        txt = open("nbu_reval.txt").read()
    except FileNotFoundError:
        return ov
    for line in txt.splitlines():
        m = re.match(r"\s*(66\d{4})\s+.*?\s+(\d+(?:,\d+)?)\s+(PMO|PE)\s*$", line)
        if m:
            ov[m.group(1)] = float(m.group(2).replace(",", "."))
    return ov
OVERLAY = load_overlay()

# ---------- audit / billing tips generator ----------
def audit_tips(rec):
    t = []
    f = rec["flags"]
    rel = rec["relaciones"]
    if f["urgencia"]:
        t.append("Urgencia (U): si se solicita de urgencia, adicionar el código 661200 en la misma prescripción.")
    if f["desuso"]:
        t.append("Práctica en desuso / por presupuesto (#): no tiene valor de U.B. de referencia; se cotiza por presupuesto.")
    if rel["incluye"]:
        t.append("INCLUYE (módulo): comprende " + ", ".join(rel["incluye"]) +
                 ". No facturar esos códigos por separado: ya están incluidos.")
    if rel["incluido_en"]:
        t.append("INCLUIDO EN: esta práctica ya está comprendida en " + ", ".join(rel["incluido_en"]) +
                 ". No facturar en simultáneo con ese/esos código(s).")
    if rel["no_incluye"]:
        t.append("NO incluye: " + ", ".join(rel["no_incluye"]) +
                 ". Si se realizan, se facturan por separado.")
    for r in rec["referencias"]:
        t.append(r["texto"])
    if f["requiere_norma"] and rec["norma"] and not (rel["incluye"] or rel["no_incluye"] or rel["incluido_en"]):
        t.append("Tiene Norma e Interpretación específica (ver detalle).")
    return t

# ---------- frecuencia / seriado ----------
FREQ_PAT = re.compile(
    r"seriad|se factura\w* \d?\d?\s?66\d{4}\s?x\s?\d|66\d{4}\s?x\s?\d|"
    r"hasta (?:tres|3|cinco|5|dos|2)|por cada|(?:una|1) vez|por d[ií]a|por a[ñn]o|anual", re.I)
def extract_frecuencia(n):
    if not n:
        return []
    txt = (n["norma"] + " " + n["interpretacion"]).strip()
    out = []
    for sent in re.split(r"(?<=[.])\s+", txt):
        s = sent.strip()
        if FREQ_PAT.search(s) and re.search(r"seriad|66\d{4}\s?x\s?\d|hasta (?:tres|3|cinco|5)|por cada|(?:una|1) vez|por d[ií]a", s, re.I):
            if len(s) > 4 and s not in out:
                out.append(s)
    return out
# curated seriado limits for the validator (máximo habitual y detalle)
SERIADO = {
    "660102": {"max": 5, "nota": "Seriado: ×3 en esputo, ×5 en orina (según material)."},
    "660468": {"max": 3, "nota": "Seriado: hasta 3 tomas de muestra (×3)."},
}

# ---------- build records ----------
records = {}
for r in catalog:
    code = r["code"]
    syns = SIN.get(code, [])
    n = NORMAS.get(code)
    refs = []
    for rn in r["ref_nums"]:
        tgt = "668" + rn if len(rn) == 3 else rn
        # ref numbers like 8332 -> norma general 668332
        tgt = "668" + rn[-3:]
        practica = NORMAS.get(tgt, {}).get("practica", "")
        refs.append({"code": rn, "target": tgt,
                     "texto": f"Ver norma general {tgt}" + (f" — {practica}" if practica else "")})
    rec = {
        "code": code,
        "nomenclador": "NBU",
        "nomenclador_full": "Nomenclador Bioquímico Único (NBU) · Versión 2012 · Actualización 2016 · CUBRA",
        "seccion": r["section"],
        "seccion_label": SECCION_LABEL[r["section"]],
        "grupo": classify(r["name"], syns),
        "nombre": r["name"],
        "sinonimos": syns,
        "abreviaturas": ABBR.get(code, []),
        "valor": {
            "ub": r["ub"],
            "unidad": "U.B. (Unidad Bioquímica)",
            "arancel": "Arancel = U.B. × valor monetario de la Unidad Bioquímica (según convenio).",
        },
        "flags": {
            "urgencia": r["urgencia"],
            "requiere_norma": r["norma"],
            "desuso": r["desuso"],
            "pcr": bool(re.search(r"\bPCR\b", r["name"])),
        },
        "referencias": refs,
        "norma": {"trabajo": n["norma"], "interpretacion": n["interpretacion"]} if n else None,
        "relaciones": {
            "incluye": n["includes"] if n else [],
            "no_incluye": n["excludes"] if n else [],
            "incluido_en": n["included_in"] if n else [],
        },
    }
    if code in OVERLAY and (r["ub"] is None or abs((r["ub"] or 0) - OVERLAY[code]) > 1e-9):
        rec["valor"]["ub_actualizado_2024"] = OVERLAY[code]
    rec["frecuencia"] = extract_frecuencia(n)
    if code in SERIADO:
        rec["seriado"] = SERIADO[code]
    rec["auditoria"] = audit_tips(rec)
    if rec.get("seriado"):
        rec["auditoria"].append("Seriado / frecuencia: " + rec["seriado"]["nota"])
    records[code] = rec

# ---------- U.B. vigente (XLS actualizado a la fecha) ----------
def seccion_por_codigo(code):
    n = int(code)
    if 660001 <= n <= 661999:
        return ("PMO", SECCION_LABEL["PMO"])
    return ("PE", SECCION_LABEL["PE"])
ub_vig_upd = ub_vig_new = 0
try:
    XLSUB = json.load(open("data/nbu_ub_vigente.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        XLSUB = json.load(open("xls_ub.json", encoding="utf-8"))
    except FileNotFoundError:
        XLSUB = []
for full, nom, ubv in XLSUB:
    if ubv is None:
        continue
    if full in records:
        records[full]["valor"]["ub_vigente"] = ubv
        ub_vig_upd += 1
    else:
        sec, seclbl = seccion_por_codigo(full)
        records[full] = {
            "code": full, "nomenclador": "NBU",
            "nomenclador_full": "Nomenclador Bioquímico Único (NBU) — U.B. vigente (actualización a la fecha)",
            "seccion": sec, "seccion_label": seclbl, "grupo": classify(nom, []),
            "nombre": nom, "sinonimos": [], "abreviaturas": [],
            "valor": {"ub": None, "ub_vigente": ubv, "unidad": "U.B. (Unidad Bioquímica)",
                      "arancel": "Arancel = U.B. × valor monetario de la Unidad Bioquímica (según convenio)."},
            "flags": {"urgencia": False, "requiere_norma": False, "desuso": False, "pcr": False},
            "referencias": [], "norma": None, "frecuencia": [],
            "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
            "auditoria": ["Práctica del NBU con U.B. vigente (actualización a la fecha)."],
        }
        ub_vig_new += 1
print(f"U.B. vigente: actualizados {ub_vig_upd} · nuevos {ub_vig_new}", file=sys.stderr)

# ---------- reverse relationships (bidirectional graph) ----------
for code, rec in records.items():
    for tgt in rec["relaciones"]["incluye"]:
        if tgt in records:
            records[tgt].setdefault("_incluido_en_calc", []).append(code)
# merge calculated "es parte de" into a derived field
for code, rec in records.items():
    calc = rec.pop("_incluido_en_calc", [])
    merged = sorted(set(rec["relaciones"]["incluido_en"] + calc))
    rec["relaciones"]["incluido_en"] = merged

# every NBU record is tagged with its nomenclador
for rec in records.values():
    rec["nomenclador"] = "NBU"

# ---------- integrate PMO 'Catálogo de Prestaciones' (medical/surgical nomenclador) ----------
PMO_CAP = {
    "01": "Sistema nervioso (cirugía)", "02": "Aparato de la visión (cirugía)",
    "03": "Otorrinolaringología (cirugía)", "04": "Sistema endócrino (cirugía)",
    "05": "Tórax (cirugía)", "06": "Mama (cirugía)", "07": "Sistema cardiovascular (cirugía)",
    "08": "Aparato digestivo y abdomen (cirugía)", "09": "Vasos y ganglios linfáticos (cirugía)",
    "10": "Aparato urinario y genital masculino (cirugía)",
    "11": "Aparato genital femenino y obstétricas (cirugía)",
    "12": "Huesos y articulaciones (traumatología)", "13": "Piel y tejido celular subcutáneo (cirugía)",
    "14": "Alergia e inmunología", "15": "Anatomía patológica", "16": "Anestesiología",
    "17": "Cardiología", "18": "Ecodiagnóstico y hemodinamia", "19": "Endocrinología y nutrición",
    "20": "Gastroenterología", "21": "Genética humana", "22": "Ginecología y obstetricia",
    "24": "Hemoterapia", "25": "Rehabilitación y kinesiología", "26": "Medicina nuclear",
    "28": "Neumonología", "29": "Neurología", "30": "Oftalmología", "31": "Otorrinolaringología",
    "32": "Pediatría", "33": "Salud mental", "34": "Radiología / Diagnóstico por imágenes",
    "35": "Radioterapia", "36": "Urología", "38": "Tratamientos especiales",
    "66": "Análisis clínicos (laboratorio)",
}
_SURG = [
    "Acto quirúrgico: honorarios del cirujano (código de la práctica).",
    "Ayudante(s) quirúrgico(s): se adicionan según la complejidad y la cantidad de ayudantes que admite el acto.",
    "Gastos: derechos de quirófano/internación y materiales o insumos según el procedimiento.",
    "Anestesia: se codifica y factura POR SEPARADO en el capítulo 16 (Anestesiología), según el acto quirúrgico.",
    "Anatomía patológica: si se remite pieza o biopsia, se factura aparte (capítulo 15).",
]
_DIAG = [
    "Honorarios profesionales de la práctica.",
    "Gastos: insumos, contraste, película o material descartable cuando corresponda.",
]
# normas generales de facturación por capítulo (orientativas — verificar contra la norma aplicable)
CHAPTER_NORMS = {p: {"que_cargar": list(_SURG), "ver_tambien": ["16", "15"]} for p in
                 ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13"]}
CHAPTER_NORMS.update({
    "14": {"que_cargar": ["Práctica de alergia (testificación/tratamiento) + material o alergenos utilizados."], "ver_tambien": []},
    "15": {"que_cargar": ["Se factura por pieza o biopsia remitida; cada material/taco corresponde a una determinación.",
                          "Complementa al acto quirúrgico (capítulo 15 se factura aparte de la cirugía)."], "ver_tambien": []},
    "16": {"que_cargar": ["Anestesia asociada al acto quirúrgico: se factura POR SEPARADO del honorario del cirujano.",
                          "Las unidades/valor dependen de la cirugía realizada."], "ver_tambien": []},
    "17": {"que_cargar": list(_DIAG), "ver_tambien": []},
    "18": {"que_cargar": ["Honorarios + gastos. En estudios con contraste o intervencionismo, los insumos pueden facturarse aparte."], "ver_tambien": []},
    "19": {"que_cargar": list(_DIAG), "ver_tambien": []},
    "20": {"que_cargar": list(_DIAG), "ver_tambien": []},
    "21": {"que_cargar": ["Estudio genético: honorarios + insumos. Puede requerir prácticas de laboratorio asociadas (NBU 66xxxx)."], "ver_tambien": []},
    "22": {"que_cargar": list(_DIAG), "ver_tambien": []},
    "24": {"que_cargar": ["Unidad transfusional + pruebas inmunohematológicas (grupo y factor, compatibilidad, Coombs) que se codifican en el NBU (66xxxx).",
                          "Cruce con la sección Laboratorio para las determinaciones asociadas."], "ver_tambien": []},
    "25": {"que_cargar": ["Se factura por sesión."], "ver_tambien": []},
    "26": {"que_cargar": ["Honorarios + radiofármaco/insumos según el estudio."], "ver_tambien": []},
    "28": {"que_cargar": list(_DIAG), "ver_tambien": []},
    "29": {"que_cargar": list(_DIAG), "ver_tambien": []},
    "30": {"que_cargar": list(_DIAG), "ver_tambien": []},
    "31": {"que_cargar": list(_DIAG), "ver_tambien": []},
    "32": {"que_cargar": ["Atención pediátrica: honorarios de la práctica/consulta."], "ver_tambien": []},
    "33": {"que_cargar": ["Se factura por sesión (individual, grupal o familiar según corresponda)."], "ver_tambien": []},
    "34": {"que_cargar": ["Honorarios + gastos. En estudios contrastados, el contraste/película puede facturarse aparte."], "ver_tambien": []},
    "35": {"que_cargar": ["Radioterapia: se factura por tratamiento/campo según la planificación."], "ver_tambien": []},
    "36": {"que_cargar": list(_DIAG), "ver_tambien": ["16"]},
    "38": {"que_cargar": ["Tratamiento especial: honorarios + insumos/medicación según el esquema."], "ver_tambien": []},
})

_TITLE = (r"Operaciones?(?: en (?:el|la|los|las))?[^,.]*?(?:nervioso|visión|Endocrino|Mama|"
          r"Tórax|Cardiovascular|Digestivo y Abdomen|linfáticos|urinario y genital|Genital "
          r"Femenino[^,.]*|huesos y articulaciones|piel y tejido)|Anatomía patológica|"
          r"Endocrinología y nutrición(?: metabolismo)?|Gastroenterología|Genética humana|"
          r"Ginecología y obstetricia|Hemoterapia|Rehabilitación médica|Medicina nuclear|"
          r"Neurología|Oftalmología|Otorrinolaringología|Pediatría|Salud mental|Radiología|"
          r"Urología|Tratamientos Especiales|Cardiología|Alergia|Análisis clínicos")
TITLE_STRIP = re.compile(r"^(?:Práctica|Normativa|" + _TITLE + r")\b[\s:]*", re.I)
NAME_FIX = {"010101": "tratamiento quirúrgico del encefalomeningocele"}

def clean_pmo_name(nm):
    nm = re.sub(r"\s+", " ", nm or "").strip()
    prev = None
    while prev != nm:
        prev = nm
        nm = TITLE_STRIP.sub("", nm).strip(" :-")
    return nm

pmo_added = pmo_linked = pmo_missing = 0
try:
    pmo = json.load(open("pmo_catalog.json", encoding="utf-8"))
except FileNotFoundError:
    pmo = None
if pmo:
    for code in pmo["order"]:
        r = pmo["records"][code]
        pref = code[:2]
        cap = PMO_CAP.get(pref, "Otras prestaciones PMO")
        nombre = NAME_FIX.get(code) or clean_pmo_name(r["nombre"]) or r["nombre"]
        if pref == "66":  # lab practice
            if code in records:  # already in NBU -> cross-link, don't duplicate
                records[code]["en_catalogo_pmo"] = True
                pmo_linked += 1
            else:  # in PMO catalog but not in this NBU version -> add as lab entry
                records[code] = {
                    "code": code, "nomenclador": "PMO",
                    "nomenclador_full": "Catálogo de Prestaciones del PMO (Res. 201/2002) — práctica de laboratorio",
                    "seccion": "PMO_MED", "seccion_label": "Catálogo PMO — laboratorio",
                    "grupo": "Análisis clínicos (laboratorio)", "nombre": nombre,
                    "sinonimos": [], "abreviaturas": [],
                    "valor": {"ub": None, "unidad": "—", "arancel": "Práctica de laboratorio del Catálogo PMO no presente en el NBU 2012/2016 cargado."},
                    "flags": {"urgencia": False, "requiere_norma": False, "desuso": False, "pcr": False},
                    "referencias": [], "norma": None, "frecuencia": [],
                    "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
                    "en_catalogo_pmo": True,
                    "auditoria": ["Práctica de laboratorio incluida en el Catálogo PMO; sin valor de U.B. en el NBU 2012/2016 cargado."],
                }
                pmo_missing += 1
            continue
        if code in records:
            continue
        records[code] = {
            "code": code, "nomenclador": "PMO",
            "nomenclador_full": "Catálogo de Prestaciones del PMO — Programa Médico Obligatorio (Resolución 201/2002, S.S. Salud)",
            "seccion": "PMO_MED", "seccion_label": "Catálogo PMO — prestaciones médicas",
            "grupo": cap, "nombre": nombre, "sinonimos": [], "abreviaturas": [],
            "valor": {"ub": None, "unidad": "—",
                      "arancel": "Prestación del Catálogo del PMO (cobertura obligatoria). El arancel surge del nomenclador/convenio aplicable, no del NBU."},
            "flags": {"urgencia": False, "requiere_norma": False, "desuso": False, "pcr": False},
            "referencias": [], "norma": None, "frecuencia": [],
            "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
            "auditoria": [
                "Prestación incluida en el Catálogo de Prestaciones del PMO — cobertura obligatoria de los Agentes del Seguro de Salud (Res. 201/2002).",
                "Capítulo / especialidad: " + cap + ".",
            ],
        }
        pmo_added += 1
print(f"PMO: agregados {pmo_added} · cruzados con NBU (66xxxx) {pmo_linked} · sin match {pmo_missing}", file=sys.stderr)

# ---------- integrate Nomenclador Nacional values (OCR, checksum-validated) ----------
def clean_nn_name(nm):
    nm = re.sub(r"\s+", " ", nm or "").strip()
    # drop boilerplate that leaks into first-on-page rows
    nm = re.split(r"OPERACIONES EN|texto retirado|extoreirado|Texto retirado", nm, flags=re.I)[-1]
    nm = re.sub(r"^[^A-ZÁÉÍÓÚÑ]*", "", nm)
    return nm.strip(" .:-")[:80] or nm[:80]

nn_added = nn_enriched = 0
try:
    NNV = json.load(open("nn_values.json", encoding="utf-8"))
except FileNotFoundError:
    NNV = {}
for code, r in NNV.items():
    if r.get("checksum_ok") is not True:
        continue
    esp, ayu, anes, gas = r["esp"], r["ayu"], r["anes"], r["gasto"]
    valores = {
        "fuente": "Nomenclador Nacional de Prestaciones Médicas (Anexo II, Res. 201/02 MS)",
        "validado": True,
        "galeno": {"especialista": esp["u"], "ayudantes_n": ayu["n"], "ayudante_c_u": ayu["u"],
                   "anestesista": anes["u"], "gasto": gas["u"]},
        "pesos_2002": {"especialista": esp["p"], "ayudantes": ayu["p"], "anestesista": anes["p"],
                       "gasto": gas["p"], "total": r["total_p"]},
        "total_2002": r["total_p"],
    }
    # concrete per-code associations (qué cargar)
    asoc = []
    if esp["u"] is not None:
        asoc.append(f"Honorario del especialista: {esp['u']:g} galenos.")
    if ayu["n"]:
        asoc.append(f"Admite {ayu['n']} ayudante(s)" + (f" ({ayu['u']:g} galenos c/u)." if ayu['u'] is not None else "."))
    if anes["u"] is not None:
        asoc.append(f"Lleva anestesia: {anes['u']:g} galenos — se factura por separado (cap. 16).")
    if gas["u"] is not None:
        asoc.append(f"Gasto quirúrgico: {gas['u']:g} galenos.")
    if code in records and records[code]["nomenclador"] == "PMO":
        records[code]["valores"] = valores
        records[code]["asociaciones_especificas"] = asoc
        nn_enriched += 1
    elif code not in records:
        pref = code[:2]
        records[code] = {
            "code": code, "nomenclador": "PMO",
            "nomenclador_full": "Nomenclador Nacional de Prestaciones Médicas (Anexo II, Res. 201/02 MS)",
            "seccion": "PMO_MED", "seccion_label": "Nomenclador Nacional — prestaciones médicas",
            "grupo": PMO_CAP.get(pref, "Otras prestaciones PMO"),
            "nombre": clean_nn_name(r["nombre_ocr"]), "sinonimos": [], "abreviaturas": [],
            "valor": {"ub": None, "unidad": "galenos",
                      "arancel": "Valorización en galenos del Nomenclador Nacional (ver honorarios y gasto)."},
            "flags": {"urgencia": False, "requiere_norma": False, "desuso": False, "pcr": False},
            "referencias": [], "norma": None, "frecuencia": [],
            "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
            "valores": valores, "asociaciones_especificas": asoc,
            "auditoria": ["Prestación del Nomenclador Nacional (Res. 201/02) con valorización en galenos."],
        }
        nn_added += 1
print(f"NN valores: enriquecidos {nn_enriched} · nuevos {nn_added}", file=sys.stderr)

# ---------- integrate dental (odontología) codes from part 3 ----------
ODO_CAP = {
    "01": "Consultas", "02": "Operatoria dental", "03": "Endodoncia", "04": "Prótesis",
    "05": "Odontología preventiva", "06": "Ortodoncia y ortopedia funcional",
    "07": "Odontopediatría", "08": "Periodoncia", "09": "Radiología odontológica",
    "10": "Cirugía y traumatología bucal",
}
ODO_NAMES = {
    "0101": "Consulta, diagnóstico, fichado y plan de tratamiento",
    "0103": "Visita / consulta a domicilio", "0104": "Consulta de urgencia",
    "0201": "Obturación de amalgama. Cavidad simple",
    "0202": "Obturación de amalgama. Cavidad compuesta o compleja",
    "0204": "Obturación con amalgama: reconstrucciones con tornillo en conducto",
    "0205": "Obturación resina autocurado. Cavidad simple",
    "0206": "Obturación resina autocurado. Cavidad compuesta o compleja",
    "0208": "Obturación resina fotocurado. Sector anterior",
    "0209": "Reconstrucción de ángulo en dientes anteriores",
    "0301": "Tratamiento endodóntico en unirradiculares",
    "0302": "Tratamiento endodóntico en multirradiculares",
    "0305": "Biopulpectomía parcial", "0306": "Necropulpectomía parcial o momificación",
    "0401": "Prótesis fija",
    "040101": "Incrustaciones: cavidad simple", "040102": "Incrustaciones: cavidad compleja o compuesta",
    "040103": "Corona forjada", "040104": "Corona colada", "040105": "Corona colada con frente estético",
    "040106": "Corona espiga", "040107": "Corona colada revestida de acrílico",
    "040108": "Perno muñón simple", "040109": "Perno muñón seccionado",
    "040110": "Tramo de puente colado", "040111": "Corona de acrílico",
    "040112": "Elemento provisorio. Por unidad",
    "040201": "Prótesis parcial removible de acrílico. Hasta cuatro dientes",
    "040202": "Prótesis parcial removible de acrílico. De cinco o más dientes",
    "040203": "Colados en cromo cobalto hasta cuatro dientes",
    "040204": "Colados en cromo cobalto de cinco o más dientes",
    "040205": "Prótesis parcial inmediata", "040303": "Prótesis completa inmediata",
    "040304": "Base colada para prótesis completa", "040401": "Compostura simple",
    "040402": "Compostura con agregado de un diente",
    "040403": "Compostura con agregado de un retenedor",
    "040404": "Compostura con agregado de un diente y un retenedor",
    "040405": "Diente subsiguiente c/u", "040406": "Retenedor subsiguiente c/u",
    "040407": "Soldado de retención en aparatos de cromo-cobalto con agregado de un diente",
    "040408": "Retención subsiguiente", "040409": "Carilla de acrílico",
    "040410": "Rebasado de prótesis, c/u", "040411": "Cubeta individual",
    "040412": "Levante de articulación, en acrílico translúcido y retenedores forjados en acero",
    "0501": "Tartrectomía y cepillado mecánico", "0502": "Consulta preventiva. Terapias fluoradas",
    "0504": "Consulta preventiva. Detección, control de placa bacteriana y enseñanza de técnicas de higiene bucal",
    "0505": "Selladores de surcos, fosas y fisuras",
    "0601": "Consulta especializada en ortodoncia de estudio",
    "0602": "Ortodoncia interceptiva. Tratamiento de la dentición primaria o mixta",
    "0603": "Tratamiento de la dentición permanente",
    "0604": "Corrección de malposiciones simples con espacio",
    "0701": "Consultas de motivación", "0702": "Mantenedor de espacio",
    "0704": "Tratamiento de dientes temporarios con formocresol",
    "0705": "Corona metálica de acero provisoria por destrucción coronaria",
    "070601": "Reducción de luxación con inmovilización dentaria",
    "070604": "Fractura amelodentinaria. Protección pulpar. Coronas provisorias",
    "0801": "Consulta de estudio. Sondaje, fichado, diagnóstico y pronóstico",
    "0802": "Tratamiento de gingivitis", "0803": "Tratamiento de enfermedad periodontal",
    "0805": "Desgaste selectivo o armonización oclusal",
    "0806": "Placas oclusales (temporarias) de acrílico removibles. Cualquier tipo",
    "1001": "Extracción dentaria", "1002": "Plástica de comunicación buco-sinusal",
    "1003": "Biopsia por punción, aspiración o escisión", "1004": "Alveolectomía estabilizadora",
    "1005": "Reimplante dentario inmediato al traumatismo con inmovilización",
    "1006": "Incisión y drenaje de abscesos", "1007": "Biopsia por escisión",
    "1009": "Extracción de dientes con retención ósea", "1010": "Germectomía",
    "1011": "Liberación de dientes retenidos", "1012": "Apicectomía",
    "1013": "Tratamiento de la osteomielitis", "1014": "Extracción de cuerpo extraño",
    "1015": "Alveolectomía correctiva",
}
def cid_to_dotted(cid):
    m = re.match(r"^(\d\d)(\d\d)(\d\d)?([A-Z])?$", cid)
    if not m:
        return cid
    parts = [m.group(1), m.group(2)] + ([m.group(3)] if m.group(3) else [])
    d = ".".join(parts)
    return d + ("." + m.group(4) if m.group(4) else "")
def clean_odo_name(nm):
    nm = re.sub(r"\s+", " ", nm or "").strip()
    nm = re.split(r"CONSULTAS|OPERATORIA DENTAL|ENDODONCIA|PROTESIS|ODONTOLOG[IÍ]A PREVENTIVA|"
                  r"ORTODONCIA|ODONTOPEDIATR|PERIODONCIA|RADIOLOG|CIRUG[IÍ]A BUCAL|"
                  r"texto retirado|extbre|edoretr|P\.M\.O\.DE", nm, flags=re.I)[-1]
    return re.sub(r"^[^A-ZÁÉÍÓÚÑa-z]*", "", nm).strip(" .:-")[:70]

odo_added = 0
try:
    ODO = json.load(open("nn_odo.json", encoding="utf-8"))["records"]
except FileNotFoundError:
    ODO = {}
for cid, r in ODO.items():
    if r["capitulo_num"] not in ODO_CAP or r["tipo"] != "priced":
        continue
    hon, gas = r["honorarios"], r["gastos"]
    if hon["p"] is None and r["valor_practica"] is None:
        continue
    rid = "ODO" + cid
    cap = ODO_CAP[r["capitulo_num"]]
    valores = {
        "fuente": "Nomenclador Nacional — Prácticas Odontológicas (Anexo II, Res. 201/02; valores a marzo 1991)",
        "validado": r["checksum_ok"] is True, "tipo": "odontologia",
        "galeno": {"honorarios": hon["u"], "gastos": gas["u"]},
        "pesos_2002": {"honorarios": hon["p"], "gastos": gas["p"], "valor_practica": r["valor_practica"]},
        "valor_practica_2002": r["valor_practica"], "coseguro_pct": r["coseguro"],
    }
    asoc = []
    if hon["u"] is not None:
        asoc.append(f"Honorario odontológico: {hon['u']:g} galenos (G.Od.).")
    if gas["u"] is not None:
        asoc.append(f"Gasto: {gas['u']:g} galenos.")
    if r["coseguro"] is not None:
        asoc.append(f"Coseguro máximo a cobrar: hasta {r['coseguro']:g}%.")
    records[rid] = {
        "code": cid_to_dotted(cid), "nomenclador": "ODO",
        "nomenclador_full": "Nomenclador Nacional de Prácticas Odontológicas (Anexo II, Res. 201/02 MS)",
        "seccion": "ODO", "seccion_label": "Odontología — " + cap,
        "grupo": cap, "nombre": ODO_NAMES.get(cid) or clean_odo_name(r["nombre_ocr"]) or r["dotted"],
        "sinonimos": [], "abreviaturas": [],
        "valor": {"ub": None, "unidad": "galenos odontológicos",
                  "arancel": "Valorización en galenos odontológicos del Nomenclador Nacional."},
        "flags": {"urgencia": False, "requiere_norma": False, "desuso": False, "pcr": False},
        "referencias": [], "norma": None, "frecuencia": [],
        "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
        "valores": valores, "asociaciones_especificas": asoc,
        "auditoria": ["Práctica odontológica del Nomenclador Nacional (Res. 201/02)."] +
                     ([f"Coseguro máximo: {r['coseguro']:g}%."] if r["coseguro"] is not None else []),
    }
    odo_added += 1
print(f"ODO (dental): agregados {odo_added}", file=sys.stderr)

# ---------- Nomenclador ÚNICO (VISITAR) + equivalencias con Prestaciones Médicas ----------
def cap_prefijo(code):
    """Prefijo de capítulo de un código.

    Los códigos del Único de 8 dígitos llevan 2 dígitos propios delante del código
    del Nomenclador Nacional (10300122 → 300122), así que el capítulo son los dígitos
    3º y 4º. Tomar los dos primeros hacía que, por ejemplo, las prácticas de
    oftalmología cayeran en «Aparato urinario y genital masculino».
    """
    code = str(code or "")
    return code[2:4] if len(code) == 8 else code[:2]


UNICO_CAP = dict(PMO_CAP)
UNICO_CAP.update({
    "40": "Internación y prácticas especiales", "41": "Aranceles globales",
    "42": "Consultas", "43": "Internación / hotelería", "50": "Módulos y trasplantes",
    "71": "Materiales", "88": "Módulos NCG (cirugía)", "90": "Cápita / atención médica",
    "99": "Medicamentos y descartables",
})
try:
    UNICO = json.load(open("data/unico_equivalencias.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        UNICO = json.load(open("unico_equivalencias.json", encoding="utf-8"))
    except FileNotFoundError:
        UNICO = []

def annot_unico(target_key, code, desc, score, tipo):
    lst = records[target_key].setdefault("equivalencia_unico", [])
    if not any(x["unico_code"] == code for x in lst):
        lst.append({"unico_code": code, "unico_key": "U" + code,
                    "unico_desc": desc, "score": score, "tipo": tipo})

unico_added = sin_equiv = pmo_annot = 0
for r in UNICO:
    code = r["unico"]
    cap = UNICO_CAP.get(cap_prefijo(code), "Otros / general")
    eq = r.get("eq")
    tiene_eq = bool(eq)
    score = r.get("score")
    equivalencia = None
    if tiene_eq:
        pmo_key = eq if (eq in records and records[eq].get("nomenclador") == "PMO") else None
        equivalencia = {
            "target_nom": "PMO", "target_label": "Prestaciones Médicas",
            "code": eq, "key": pmo_key,
            "desc": r.get("eq_desc") or (records[eq]["nombre"] if pmo_key else ""),
            "score": score,
        }
        if pmo_key:
            annot_unico(pmo_key, code, r["unico_desc"], score, "med")
            pmo_annot += 1
        pct = f" (similitud {round(score * 100)}%)." if score is not None else "."
        audit = "Equivale a la práctica " + eq + " del Nomenclador de Prestaciones Médicas" + pct
    else:
        sin_equiv += 1
        audit = "Sin equivalencia hallada en Prestaciones Médicas — pendiente de mapeo manual."
    # Igual que en la parte de laboratorio: la planilla pega al nombre de la
    # práctica encabezados de observación / cobertura. El parser ya los separó.
    med_extra = {}
    if r.get("unico_obs"):
        med_extra["observacion_unico"] = r["unico_obs"]
    if r.get("marcador"):
        med_extra["marcador_unico"] = r["marcador"]
    if r.get("truncado"):
        med_extra["texto_truncado"] = True
    records["U" + code] = {
        "code": code, "nomenclador": "UNICO", "unico_tipo": "med",
        "nomenclador_full": "Nomenclador ÚNICO (VISITAR SRL) — prestaciones médicas · en elaboración",
        "seccion": "UNICO", "seccion_label": "Único — " + cap,
        "grupo": cap, "nombre": r["unico_desc"] or code, **med_extra,
        "sinonimos": [], "abreviaturas": [],
        "valor": {"ub": None, "unidad": "—",
                  "arancel": "Nomenclador ÚNICO en elaboración (sin valorización cargada)."},
        "flags": {"urgencia": False, "requiere_norma": False, "desuso": False, "pcr": False},
        "referencias": [], "norma": None, "frecuencia": [],
        "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
        "equivalencia": equivalencia, "sin_equivalencia": (not tiene_eq),
        "auditoria": [audit],
    }
    # heredar de la prestación médica equivalente las asociaciones específicas y flags
    if pmo_key:
        src = records[pmo_key]
        if src.get("asociaciones_especificas"):
            records["U" + code]["asociaciones_especificas"] = list(src["asociaciones_especificas"])
        if src.get("valores"):
            records["U" + code]["valores"] = src["valores"]
        records["U" + code]["flags"] = dict(src.get("flags", records["U" + code]["flags"]))
    unico_added += 1
print(f"UNICO médico: agregados {unico_added} · con equiv {unico_added - sin_equiv} · sin equiv {sin_equiv} · PMO anotados {pmo_annot}", file=sys.stderr)

# ---------- ÚNICO médico — códigos agregados con equivalencia a Prestaciones Médicas (planilla manual) ----------
try:
    UNICO_MED_EXTRA = json.load(open("data/unico_med_extra.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        UNICO_MED_EXTRA = json.load(open("unico_med_extra.json", encoding="utf-8"))
    except FileNotFoundError:
        UNICO_MED_EXTRA = []
extra_added = extra_annot = extra_sin = 0
for r in UNICO_MED_EXTRA:
    code = r["unico"]
    ukey = "U" + code
    if ukey in records:
        continue
    pm = (r.get("pm") or "").strip()
    tiene_eq = bool(pm)
    if tiene_eq:
        pm_key = pm if (pm in records and records[pm].get("nomenclador") == "PMO") else None
        cap = UNICO_CAP.get(pm[:2], "Otros / general")
        equivalencia = {
            "target_nom": "PMO", "target_label": "Prestaciones Médicas",
            "code": pm, "key": pm_key,
            "desc": r.get("pm_desc") or (records[pm]["nombre"] if pm_key else ""),
            "score": None,
        }
        if pm_key:
            annot_unico(pm_key, code, r["nombre"], None, "med")
            extra_annot += 1
        audit = ["Equivale a la práctica " + pm + " del Nomenclador de Prestaciones Médicas" +
                 ("." if pm_key else " (sin ficha propia cargada).")]
    else:
        equivalencia = None
        cap = classify(r["nombre"], [])
        audit = ["Sin equivalencia en Prestaciones Médicas — pendiente de mapeo manual."]
        extra_sin += 1
    extra_extra = {}
    if r.get("observacion"):
        extra_extra["observacion_unico"] = r["observacion"]
    if r.get("marcador"):
        extra_extra["marcador_unico"] = r["marcador"]
    if r.get("truncado"):
        extra_extra["texto_truncado"] = True
    records[ukey] = {
        "code": code, "nomenclador": "UNICO", "unico_tipo": "med",
        "nomenclador_full": "Nomenclador ÚNICO (VISITAR SRL) — prestación agregada",
        "seccion": "UNICO", "seccion_label": "Único — " + cap,
        "grupo": cap, "nombre": r["nombre"] or code, **extra_extra,
        "sinonimos": [], "abreviaturas": [],
        "valor": {"ub": None, "unidad": "—",
                  "arancel": "Nomenclador ÚNICO en elaboración (sin valorización cargada)."},
        "flags": {"urgencia": False, "requiere_norma": False, "desuso": False, "pcr": False},
        "referencias": [], "norma": None, "frecuencia": [],
        "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
        "equivalencia": equivalencia, "sin_equivalencia": (not tiene_eq),
        "auditoria": audit,
    }
    unico_added += 1
    extra_added += 1
print(f"UNICO médico (agregados manuales): {extra_added} · PMO anotados {extra_annot} · sin equiv {extra_sin}", file=sys.stderr)

# ---------- Nomenclador ÚNICO — Laboratorio (VISITAR) : prefijo(2) + código NBU(6) ----------
try:
    UNICO_LAB = json.load(open("data/unico_lab.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        UNICO_LAB = json.load(open("unico_lab.json", encoding="utf-8"))
    except FileNotFoundError:
        UNICO_LAB = []

lab_added = lab_annot = lab_nofit = 0
nbu_to_ulab = {}   # NBU code -> ÚNICO-lab _key (para traducir relaciones/parentesco)
for r in UNICO_LAB:
    code = r["unico"]
    nbu = r["nbu"]
    ub = r.get("ub")
    ukey = "U" + code
    nbu_key = nbu if (nbu in records and records[nbu].get("nomenclador") == "NBU") else None
    if nbu_key:
        grupo = records[nbu_key].get("grupo") or "Laboratorio"
        annot_unico(nbu_key, code, r["nombre"], None, "lab")
        nbu_to_ulab[nbu] = ukey
        lab_annot += 1
    else:
        grupo = classify(r["nombre"], [])
        lab_nofit += 1
    equivalencia = {
        "target_nom": "NBU", "target_label": "Laboratorio (NBU)",
        "code": nbu, "key": nbu_key,
        "desc": records[nbu]["nombre"] if nbu_key else "",
        "score": None,
    }
    # La planilla del Único mezcla en la misma celda el nombre de la práctica, un
    # marcador de clasificación —(PMO AA), (NO PMO BF NC)…— y a veces una
    # observación. El parser ya los separó: acá se guardan en campos propios para
    # que el título de la ficha sea sólo el nombre de la práctica.
    lab_extra = {}
    if r.get("marcador"):
        lab_extra["marcador_unico"] = r["marcador"]
    if r.get("observacion"):
        lab_extra["observacion_unico"] = r["observacion"]
    if r.get("truncado"):
        lab_extra["texto_truncado"] = True
    records[ukey] = {
        "code": code, "nomenclador": "UNICO", "unico_tipo": "lab",
        "nomenclador_full": "Nomenclador ÚNICO (VISITAR SRL) — laboratorio (equivalente al NBU)",
        "seccion": "UNICO", "seccion_label": "Único — Laboratorio · " + grupo,
        "grupo": grupo, "nombre": r["nombre"], **lab_extra,
        "sinonimos": [], "abreviaturas": [],
        "valor": {"ub": ub, "unidad": "U.B. (Unidad Bioquímica)",
                  "arancel": "Arancel = U.B. × valor monetario de la Unidad Bioquímica (según convenio)."},
        "flags": {"urgencia": False, "requiere_norma": False, "desuso": False, "pcr": False},
        "referencias": [], "norma": None, "frecuencia": [],
        "relaciones": {"incluye": [], "no_incluye": [], "incluido_en": []},
        "equivalencia": equivalencia, "sin_equivalencia": False,
        "_nbu_src": nbu_key,
        "auditoria": [],
    }
    unico_added += 1
    lab_added += 1

# Propagar la inteligencia del NBU a la parte de laboratorio del Único
# (relaciones/parentesco, módulos, norma, seriado, flags, auditoría).
def _xlate(codes):
    """Traduce códigos NBU referidos a su equivalente ÚNICO-lab (si existe); si no, deja el código NBU."""
    return [nbu_to_ulab.get(x, x) for x in codes]

prop_rel = prop_norm = prop_seri = 0
for r in UNICO_LAB:
    ukey = "U" + r["unico"]
    rec = records[ukey]
    src = rec.pop("_nbu_src", None)
    base_audit = ["Práctica de laboratorio del Nomenclador Único. Equivale al código NBU " + r["nbu"] +
                  ("." if src else " (sin ficha propia cargada en el NBU).")]
    if not src:
        rec["auditoria"] = base_audit
        continue
    s = records[src]
    rec["flags"] = dict(s.get("flags", rec["flags"]))
    rec["norma"] = s.get("norma")
    if s.get("norma"):
        prop_norm += 1
    rec["frecuencia"] = list(s.get("frecuencia", []))
    if s.get("seriado"):
        rec["seriado"] = s["seriado"]
        prop_seri += 1
    rel = s.get("relaciones", {})
    rec["relaciones"] = {
        "incluye": _xlate(rel.get("incluye", [])),
        "no_incluye": _xlate(rel.get("no_incluye", [])),
        "incluido_en": _xlate(rel.get("incluido_en", [])),
    }
    if any(rec["relaciones"].values()):
        prop_rel += 1
    # auditoría: nota de equivalencia + las normas heredadas del NBU
    rec["auditoria"] = base_audit + list(s.get("auditoria", []))
print(f"UNICO lab: agregados {lab_added} · NBU anotados {lab_annot} · sin ficha NBU {lab_nofit}", file=sys.stderr)
print(f"UNICO lab propagado del NBU: relaciones {prop_rel} · normas {prop_norm} · seriados {prop_seri}", file=sys.stderr)

# ---------- glossary / metadata ----------
glossary = {
    "U": "Urgencia: práctica clasificada para casos de urgencia. Al incluirse en una prescripción, se debe adicionar el código 661200.",
    "N": "Ver Anexo de Normas Específicas e Interpretaciones para este código.",
    "(#)": "Por presupuesto: prácticas en desuso que no tienen valores de referencia (U.B.).",
    "PCR": "Determinación por metodología de Reacción en Cadena de la Polimerasa.",
    "U.B.": "Unidad Bioquímica: variable disparadora del arancel. Arancel = U.B. × valor de la U.B.",
    "N8327": "Ver norma/interpretación del código 668327 (Pesticidas nitrogenados).",
    "N8332": "Ver norma/interpretación del código 668332 (Pesticidas organoclorados).",
    "N8337": "Ver norma/interpretación del código 668337 (Pesticidas organofosforados).",
    "661200": "URGENCIAS: se adiciona a toda prescripción de urgencia (una vez, independiente de la cantidad de prácticas).",
    "660001": "ACTO BIOQUÍMICO (AB): se aplica 1 vez por prescripción, cubre etapas pre/post-analíticas.",
    "661001": "ACTO BIOQUÍMICO DE INTERNACIÓN (ABI): 1 por día de internación.",
    "662001": "ABC — ACTO BIOQUÍMICO COMPLEMENTARIO: adicional en pruebas de sobrecarga/estímulo/inhibición.",
}
leyes = [
    {"ley": "15465", "titulo": "Enfermedades de notificación obligatoria", "sancion": "29/09/1960"},
    {"ley": "22990", "titulo": "Ley de Sangre", "sancion": "20/11/1983"},
    {"ley": "23798", "titulo": "Ley de Sida", "sancion": "16/08/1990"},
    {"ley": "24901", "titulo": "Sistema de prestaciones básicas para personas con discapacidad", "sancion": "05/11/1997",
     "resumen": "Instituye un sistema de prestaciones básicas de atención integral (prevención, asistencia, promoción y protección) a favor de las personas con discapacidad.",
     "cobertura": "Cobertura total y obligatoria por las obras sociales de las prestaciones básicas que necesiten las personas con discapacidad afiliadas: prestaciones preventivas, de rehabilitación, terapéutico-educativas, asistenciales y de transporte, entre otras.",
     "articulos": [
        "Art. 1° — Instituye el sistema de prestaciones básicas de atención integral a favor de las personas con discapacidad.",
        "Art. 2° — Las obras sociales (ley 23.660) tienen a su cargo, con carácter obligatorio, la cobertura total de las prestaciones básicas.",
        "Art. 6° y ss. — Prestaciones: preventivas, de rehabilitación, terapéutico-educativas, asistenciales y de apoyo (incluye transporte).",
     ],
     "temas": ["discapacidad", "rehabilitación", "certificado único de discapacidad"],
     "codigos": ["250102", "250104", "250106", "330101", "170117"]},
    {"ley": "25326", "titulo": "Protección de Datos Personales", "sancion": "04/10/2000"},
    {"ley": "25543", "titulo": "Test HIV obligatorio a embarazadas", "sancion": "27/11/2001"},
    {"ley": "26279", "titulo": "Pesquisa Neonatal", "sancion": "08/08/2007"},
    {"ley": "26281", "titulo": "Prevención y Control del Chagas", "sancion": "08/08/2007"},
    {"ley": "26369", "titulo": "Detección de estreptococo Grupo B a embarazadas", "sancion": "16/04/2008"},
    {"ley": "26529", "titulo": "Derechos del Paciente", "sancion": "21/10/2009"},
    {"ley": "26588", "titulo": "Enfermedad Celíaca", "sancion": "02/12/2009",
     "resumen": "Declara de interés nacional la atención, investigación, detección temprana, diagnóstico y tratamiento de la enfermedad celíaca, su difusión y el acceso a alimentos libres de gluten. Modificada por la Ley 27.196 y reglamentada por el Decreto 218/2023.",
     "cobertura": "Las obras sociales y prepagas deben cubrir la determinación de anticuerpos para el diagnóstico y seguimiento, y el costo de harinas y premezclas libres de gluten (monto actualizado por el Ministerio de Salud). Incluida en el PMO.",
     "articulos": [
        "Art. 1° — Interés nacional en la detección temprana, diagnóstico, tratamiento y difusión de la enfermedad celíaca.",
        "Art. 9° — Cobertura asistencial por obras sociales y prepagas (estudios de diagnóstico y control).",
        "Reglamentación: Decreto 218/2023 (deroga el Decreto 528/2011).",
     ],
     "temas": ["celiaquía", "gluten", "enfermedad celíaca", "TACC"],
     "codigos": ["669622", "669631", "664632", "664640", "665572", "665580", "665576", "665583", "666445"]},
    {"ley": "26862", "titulo": "Fertilización Humana Asistida", "sancion": "05/06/2013",
     "resumen": "Regula el acceso integral de las personas a las Técnicas de Reproducción Humana Asistida, de baja y alta complejidad, con o sin donación de gametos y/o embriones.",
     "cobertura": "Cobertura obligatoria e integral en el PMO (sector público, obras sociales y prepagas): diagnóstico, medicamentos y procedimientos y técnicas de reproducción médicamente asistida. Toda persona mayor de edad, con consentimiento informado.",
     "articulos": [
        "Art. 1° — De orden público; regula la utilización y el acceso a las Técnicas de Reproducción Humana Asistida.",
        "Art. 2° — Toda persona capaz, mayor de edad, puede acceder con consentimiento informado (Ley 26.529).",
        "Art. 8° — Cobertura obligatoria e integral; queda incluida en el Programa Médico Obligatorio (PMO).",
     ],
     "temas": ["fertilidad", "infertilidad", "reproducción asistida", "FIV", "ICSI"],
     "codigos": ["660370", "660612", "660300", "660758", "660759", "660863", "660298"]},
    {"ley": "27232", "titulo": "Ley NBU (aplicación obligatoria nacional)", "sancion": "26/11/2015"},
    {"ley": "27305", "titulo": "Leche Medicamentosa", "sancion": "26/10/2016",
     "resumen": "Incorpora al PMO la cobertura integral de leche medicamentosa para personas con alergia a la proteína de la leche vacuna (APLV) y con desórdenes, enfermedades o trastornos gastrointestinales y enfermedades metabólicas.",
     "cobertura": "Cobertura integral (100%) de la leche medicamentosa, sin límite de edad, con la prescripción del médico especialista. Obligatoria para obras sociales (leyes 23.660/23.661), prepagas y demás agentes de salud. Incluida en el PMO.",
     "articulos": [
        "Art. 1° — Incorpora como prestación obligatoria del PMO la cobertura integral de leche medicamentosa (APLV, trastornos gastrointestinales y enfermedades metabólicas).",
        "Art. 2° — Beneficiario: cualquier paciente, sin límite de edad, con prescripción del médico especialista.",
        "Art. 3° — La autoridad de aplicación determina las características de la leche medicamentosa cubierta.",
     ],
     "temas": ["APLV", "leche medicamentosa", "alergia proteína leche vacuna", "enfermedades metabólicas"], "codigos": []},
    {"ley": "27696", "titulo": "Abordaje integral de víctimas de violencia de género (PMO)", "sancion": "26/10/2022",
     "resumen": "Incorpora al Programa Médico Obligatorio de las Obras Sociales Nacionales un protocolo para el abordaje integral de las personas víctimas de violencia de género.",
     "cobertura": "Cobertura total e integral de las prácticas preventivas y terapéuticas: terapias médicas, psicológicas, psiquiátricas, farmacológicas, quirúrgicas y toda otra atención necesaria o pertinente.",
     "articulos": [
        "Art. 1° — Incorpora al PMO un protocolo para el abordaje integral de víctimas de violencia de género, con cobertura total e integral de prácticas preventivas y terapéuticas.",
        "Art. 2° — Las obras sociales y prestadores deben articular con las instancias nacionales, provinciales y locales de atención de la violencia de género.",
        "Art. 3° — Cobertura como prestación obligatoria (incluye salud mental y farmacológica).",
     ],
     "temas": ["violencia de género", "salud mental", "abordaje integral"],
     "codigos": ["330101", "330102", "330103"]},
    {"ley": "310/2004", "etiqueta": "Res. 310/2004", "titulo": "Modificación del PMO — Programa Médico Obligatorio de Emergencia (PMOE)", "sancion": "15/04/2004",
     "resumen": "Modifica la Resolución 201/2002: aprueba el Programa Médico Obligatorio de Emergencia (PMOE), conjunto de prestaciones básicas esenciales garantizadas por los Agentes del Seguro de Salud.",
     "cobertura": "Define las prestaciones básicas del PMOE y la cobertura de medicamentos; disminuye el coseguro a cargo de los beneficiarios para tratamientos con fármacos de uso permanente y/o recurrente (patologías crónicas de alto impacto sanitario y socioeconómico).",
     "articulos": [
        "Aprueba el PMOE integrado por el conjunto de prestaciones básicas esenciales.",
        "Reduce coseguros para tratamientos crónicos con medicación permanente/recurrente.",
        "Modifica y complementa la Resolución 201/2002 (PMO).",
     ],
     "temas": ["PMO", "PMOE", "coseguro", "medicamentos"], "codigos": []},
    {"ley": "HPGD", "etiqueta": "Anexo II · HPGD", "titulo": "Normas de facturación — Hospitales Públicos de Gestión Descentralizada", "sancion": "",
     "resumen": "Normas de facturación del régimen de Hospitales Públicos de Gestión Descentralizada (HPGD): reglas de los módulos clínico-quirúrgicos, permanencia, horarios y adicionales.",
     "cobertura": "Los módulos clínico-quirúrgicos comprenden todos los servicios para el diagnóstico y tratamiento del paciente durante la internación; sólo se adicionan otras prestaciones en casos expresamente indicados o con acuerdo de partes.",
     "articulos": [
        "1) Los módulos comprenden todos los servicios de diagnóstico y tratamiento durante la internación.",
        "2) Si el paciente con egreso no es retirado dentro de las 24 h, se factura un módulo clínico por día de permanencia.",
        "3) Las prestaciones en horario nocturno y/o feriado no modifican los aranceles.",
     ],
     "temas": ["hospital público", "HPGD", "módulos", "facturación", "internación"], "codigos": []},
    {"ley": "2820/2022", "etiqueta": "Res. 2820/2022", "titulo": "Diabetes — Normas de provisión de medicamentos e insumos", "sancion": "14/11/2022",
     "resumen": "Actualiza, en el marco de la Ley 23.753 (y su modificatoria 26.914), las Normas de Provisión de Medicamentos e Insumos para personas con diabetes.",
     "cobertura": "Cobertura de insulinas, hipoglucemiantes, tiras reactivas y demás insumos necesarios para el tratamiento y el control evolutivo de la diabetes. Incluida en el PMO.",
     "articulos": [
        "Establece el listado y las condiciones de provisión de medicamentos e insumos para diabetes.",
        "Marco: Ley 23.753 (asegura a las personas con diabetes los medios terapéuticos y de control).",
     ],
     "temas": ["diabetes", "insulina", "tiras reactivas", "glucemia"],
     "codigos": ["660412", "660413", "661070", "660543"]},
    {"ley": "3437/2021", "etiqueta": "Res. 3437/2021", "titulo": "Pubertad precoz central — cobertura de diagnóstico y tratamiento", "sancion": "03/12/2021",
     "resumen": "Incorpora la cobertura del diagnóstico y tratamiento de la pubertad precoz central (PPC) —análogos de GnRH— en el marco de la Res. 201/02 (PMO).",
     "cobertura": "Cobertura del tratamiento con análogos de GnRH y de los estudios de diagnóstico y seguimiento hormonal (LH, FSH, esteroides sexuales, test de estímulo).",
     "articulos": [
        "Reconoce la PPC (reactivación prematura del generador de pulsos de GnRH) y su cobertura.",
        "Diagnóstico basado en LH/FSH y esteroides sexuales; tratamiento con análogos de GnRH.",
     ],
     "temas": ["pubertad precoz", "GnRH", "endocrinología pediátrica"],
     "codigos": ["660612", "660370", "660863", "660300"]},
    {"ley": "27610", "titulo": "Acceso a la Interrupción Voluntaria del Embarazo (IVE)", "sancion": "30/12/2020",
     "resumen": "Regula el acceso a la interrupción voluntaria del embarazo (hasta la semana 14 inclusive) y a la interrupción legal (ILE), y la atención postaborto, en todo el sistema de salud.",
     "cobertura": "Cobertura obligatoria e integral de la IVE/ILE y la atención postaborto por el sector público, las obras sociales y las entidades de medicina prepaga. Incluida en el PMO.",
     "articulos": [
        "Art. 1° — Objeto: regular el acceso a la IVE y a la atención postaborto.",
        "Art. 4° — Derecho a acceder a la interrupción hasta la semana 14 inclusive del proceso gestacional.",
        "Art. 12 — Cobertura: incorporada al PMO; cobertura integral y gratuita.",
     ],
     "temas": ["IVE", "ILE", "salud sexual y reproductiva", "postaborto"],
     "codigos": ["661170", "661175", "660433", "660475"]},
    {"ley": "340/2026", "etiqueta": "Res. 340/2026", "titulo": "Discapacidad — actualización de aranceles del Sistema de Prestaciones Básicas", "sancion": "27/02/2026",
     "resumen": "Actualiza los valores de los aranceles vigentes del Sistema de Prestaciones de Atención Integral a favor de las Personas con Discapacidad (Ley 24.901 / 27.793), y reconoce el adicional por zona desfavorable (Patagonia).",
     "cobertura": "Nuevos valores de arancel de las prestaciones básicas de discapacidad; adicional del 20% sobre el arancel básico por zona desfavorable (provincias patagónicas).",
     "articulos": [
        "Actualiza los aranceles del Sistema de Prestaciones Básicas (Acta del Directorio del Sistema).",
        "Adicional del 20% por zona desfavorable (Patagonia) sobre el arancel básico.",
     ],
     "temas": ["discapacidad", "aranceles", "zona desfavorable"], "codigos": []},
    {"ley": "438/2021", "etiqueta": "Decreto 438/2021", "titulo": "Obras sociales — libre elección del Agente del Seguro de Salud", "sancion": "06/07/2021",
     "resumen": "Modifica el Decreto 504/1998 sobre el derecho de los beneficiarios y beneficiarias a la libre elección del Agente del Seguro de Salud (opción de cambio de obra social), simplificando el trámite mediante la plataforma de Trámites a Distancia (TAD).",
     "cobertura": "Regula el ejercicio del derecho a elegir y cambiar de obra social (Agente del Seguro de Salud), garantizando la continuidad de la cobertura durante el proceso.",
     "articulos": [
        "Consagra/actualiza el derecho a la libre elección del Agente del Seguro de Salud (Decretos 9/93 y 1301/97).",
        "Simplifica el trámite de opción de cambio mediante la plataforma TAD (Gestión Documental Electrónica).",
     ],
     "temas": ["obras sociales", "libre elección", "opción de cambio", "seguro de salud"], "codigos": []},
]

# valores del nomenclador de discapacidad (Ley 24.901) — actualización vigente
try:
    _disc = json.load(open("data/disc_valores.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        _disc = json.load(open("disc_valores.json", encoding="utf-8"))
    except FileNotFoundError:
        _disc = None
if _disc:
    for _l in leyes:
        if _l["ley"] == "24901":
            _l["valores"] = _disc

# CIE-10 (diagnósticos) + relaciones diagnóstico -> prácticas
try:
    CIE10 = json.load(open("data/cie10.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        CIE10 = json.load(open("cie10.json", encoding="utf-8"))
    except FileNotFoundError:
        CIE10 = {"codigos": {}, "capitulos": [], "relaciones": {}}

# ---------- PMO: cobertura obligatoria, topes y títulos limpios (ANEXO I y II, Res. 201/02) ----------
try:
    PMOCOB = json.load(open("data/pmo_cobertura.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        PMOCOB = json.load(open("pmo_cobertura.json", encoding="utf-8"))
    except FileNotFoundError:
        PMOCOB = {"codigos": {}, "generalidades": [], "topes": []}
pmo_fix = pmo_cob = 0
for _code, _info in PMOCOB.get("codigos", {}).items():
    _r = records.get(_code)
    if not _r:
        continue
    if _r.get("nomenclador") == "PMO":
        if len(_r["nombre"]) > 90 and _info.get("titulo") and len(_info["titulo"]) < len(_r["nombre"]):
            _r["nombre"] = _info["titulo"]; pmo_fix += 1
    # La cobertura se aplica a cualquier nomenclador, no sólo al PMO: 12 prácticas de
    # laboratorio (PSA, hepatitis, marcadores tumorales, rubéola…) traen su obligación
    # de cobertura acá y se estaban descartando por venir bajo un código del NBU.
    if _info.get("cobertura"):
        _r["cobertura_pmo"] = _info["cobertura"]
        # El texto puede ser una obligación de cobertura o una observación sobre
        # cuándo corresponde o no hacer el estudio: se distinguen para mostrarlos
        # con el encabezado que corresponde.
        _r["cobertura_tipo"] = ("obligacion"
                                if re.match(r"\s*obligaci[oó]n\s+de\s+cobertura", _info["cobertura"], re.I)
                                else "observacion")
        pmo_cob += 1
# ---------- Oftalmología: reparación de títulos y lateralidad ----------
# El texto del PDF del PMO viene bien escrito pero **mal cortado entre códigos**: la
# cola de una práctica queda pegada al comienzo de la siguiente (300117 perdía
# "afectados", que aparecía al inicio de 300118). El OCR del Nomenclador Nacional, en
# cambio, asigna bien el texto a cada código aunque las palabras salgan pegadas.
# Alineando ambos flujos se recupera el corte correcto. Se arbitra con el OCR del
# propio Nacional y, cuando no alcanza, con el nombre del Único para el mismo código.
# No se redacta texto nuevo: siempre se elige entre las denominaciones ya existentes.
import difflib as _dl

PMO_REC = (pmo or {}).get("records", {})
PMO_ORDER = (pmo or {}).get("order", [])
# El corrimiento de títulos y las observaciones de lateralidad no son exclusivos de
# oftalmología: se recorren todos los capítulos del Nacional. La alineación se hace
# capítulo por capítulo para que un capítulo con OCR pobre no arrastre al siguiente.
CAP_PREFIJOS = sorted({c[:2] for c in PMO_ORDER})

_OCR_RUIDO = [
    r"P?M?O?DEINTERVENCIONESQUIR[A-Z]{0,3}RGICASCONNOMENCLADORNACIONAL",
    r"P?M?O?DEPRACTICASESPECIALIZADASCONNOMENCLADORNA[A-Z]*",
    r"[A-Z]{0,4}TO?RE[TFI][IR]{0,2}[AD]{0,3}O?POR?E?L?PM[OD]",   # "texto retirado por el PMO"
    r"OPERACIONESEN[A-Z]*",
    r"OTROSDEOFTALMOLOGIA",
]


def _sinac(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _letras(s):
    return re.sub(r"[^A-Za-z]", "", _sinac(s)).upper()


def _ocr_ref(code):
    """Firma en letras del título según el OCR del Nacional, sin encabezados ni ruido.

    Se corta también en el texto de cobertura: si la firma lo incluyera, un recorte
    que se comiera el título del código siguiente parecería coincidir mejor que el
    título correcto (pasaba en 070114 y 180301).
    """
    crudo = (NNV.get(code) or {}).get("nombre_ocr", "") if NNV else ""
    # El título es la primera oración: el OCR mete a continuación el detalle que el
    # PMO retiró y, en algunas celdas, hasta el título del código siguiente (070114
    # trae también el de 070115). Se corta en el primer punto seguido de espacio,
    # exigiendo letras antes para no partir siglas como "P.M.O.".
    crudo = re.split(r"(?<=[A-Za-z][A-Za-z][A-Za-z])\.\s", crudo)[0]
    t = _letras(crudo)
    for r in _OCR_RUIDO:
        t = re.sub(r, "", t)
    t = re.split(r"OB[LU]?[IG]?[AG]?[CS]?ION[ED]{0,2}CO[EB]{1,2}ERTURA|DECOBERTURAENLOSSIGUIENTES", t)[0]
    return t


def _lateralidad(code):
    """Bilateral / Unilateral tal como lo anota el Nomenclador Nacional.

    El OCR devuelve las palabras pegadas al resto del texto ("…PMOBILATERAL"), así
    que se busca sobre el flujo de letras y no por palabra. Se aceptan además las
    formas a las que el OCR les comió la última letra ("BILATERA").
    """
    t = _letras((NNV.get(code) or {}).get("nombre_ocr", "") if NNV else "")
    if "UNIOBILATERAL" in t:
        return "Uni o bilateral"
    for largo, corto, val in (("BILATERAL", "BILATERA", "Bilateral"),
                              ("UNILATERAL", "UNILATERA", "Unilateral")):
        if largo in t or corto in t:
            return val
    return None


def _titulos_realineados(prefijos):
    """Recorta el flujo de texto del PDF usando los límites que marca el OCR."""
    codes = [c for c in PMO_ORDER if c[:2] in prefijos and c in PMO_REC]
    legible = " ".join((PMO_REC[c].get("nombre") or "") for c in codes)
    legible = re.sub(r"(\w)-\s+(\w)", r"\1\2", legible)      # des-hifenar tras unir
    legible = " ".join(legible.split())
    A = _letras(legible)
    idx = [i for i, ch in enumerate(legible) if re.match(r"[A-Za-z]", _sinac(ch))]
    B, bordes = "", []
    for c in codes:
        o = _ocr_ref(c)
        bordes.append((c, len(B), len(o) >= 6))
        B += o
    bloques = _dl.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks()

    def _mapa(b0):
        for a, b, n in bloques:
            if b + n > b0:
                return a + max(0, b0 - b)
        return len(A)

    cortes, last = [], -1
    for c, b0, ok in bordes:
        a0 = _mapa(b0) if ok else None
        if a0 is not None:
            a0 = max(a0, last)
            last = a0
        cortes.append([c, a0])
    out = {}
    for i, (c, a0) in enumerate(cortes):
        if a0 is None:
            continue
        a1 = next((cortes[j][1] for j in range(i + 1, len(cortes))
                   if cortes[j][1] is not None and cortes[j][1] > a0), None)
        s = idx[a0] if a0 < len(idx) else len(legible)
        e = idx[a1] if (a1 is not None and a1 < len(idx)) else len(legible)
        # El corte puede caer dentro de una palabra ("radiol|ogía"): se lleva al
        # espacio más cercano para no dejar sílabas sueltas en el título.
        def _esletra(i):
            return 0 <= i < len(legible) and bool(re.match(r"[A-Za-z]", _sinac(legible[i])))
        if _esletra(s) and _esletra(s - 1):
            _sig = legible.find(" ", s)
            s = (_sig + 1) if _sig != -1 else s
        if _esletra(e) and _esletra(e - 1):
            while _esletra(e):          # completar la palabra, no cortarla
                e += 1
        t = " ".join(legible[s:e].split()).strip(" ,;.-")
        if t:
            out[c] = t
    return out


def _sim(cand, ref):
    lc = _letras(cand)
    if not lc or not ref:
        return 0.0
    return _dl.SequenceMatcher(None, lc, ref[:len(lc) + 12], autojunk=False).ratio()


# "… de cobertura en los siguientes casos:" es el encabezado del texto de cobertura,
# no parte de la denominación de la práctica.
_RE_COB = re.compile(r"\s*(?:de\s+)?cobertura(?:\s+en\s+los\s+siguientes\s+casos)?\s*:.*$", re.I)

_realineados = {}
for _pref in CAP_PREFIJOS:
    _realineados.update(_titulos_realineados({_pref}))
_uni_por_codigo = {r["code"]: r["nombre"] for r in records.values()
                   if r.get("nomenclador") == "UNICO"}
oft_fix = oft_rev = oft_lat = 0
for _code, _r in records.items():
    if _r.get("nomenclador") != "PMO":
        continue
    _lat = _lateralidad(_code)
    if _lat:
        _r["lateralidad"] = _lat
        oft_lat += 1
    _ref = _ocr_ref(_code)
    _cands = [("actual", _r["nombre"]),
              ("realineado", _realineados.get(_code, "")),
              ("unico", _uni_por_codigo.get(_code, ""))]
    _cands = [(k, _RE_COB.sub("", v).strip(" ,;.-")) for k, v in _cands if v]
    _cands = [(k, v) for k, v in _cands if v]
    # En los capítulos con OCR pobre el recorte puede tragarse el texto de cobertura
    # del código siguiente. Un título no puede ser desproporcionado frente a la firma
    # que dejó el OCR: si lo es, se descarta ese candidato.
    if len(_ref) >= 6:
        _cands = [(k, v) for k, v in _cands
                  if k != "realineado" or len(_letras(v)) <= max(3 * len(_ref), 60)]
    if len(_ref) >= 6 and _cands:
        _sc = {k: _sim(v, _ref) for k, v in _cands}
        # El nombre del Único suele venir sin tildes: para desplazar al título actual
        # tiene que ser claramente mejor, no apenas mejor, y así no se pierde la
        # acentuación por una diferencia marginal.
        _sc_orden = dict(_sc)
        if "unico" in _sc_orden:
            _sc_orden["unico"] -= 0.05
        _best = max(_cands, key=lambda kv: (_sc_orden[kv[0]], kv[0] == "actual"))
        if _sc[_best[0]] < 0.55:
            _r["titulo_revisar"] = True
            oft_rev += 1
            _elegido = None
        else:
            _elegido = _best
    else:
        # Sin firma de OCR utilizable, el Único es la única denominación limpia.
        _elegido = ("unico", _uni_por_codigo[_code]) if _uni_por_codigo.get(_code) else None
    if _elegido:
        _nuevo = clean_pmo_name(_RE_COB.sub("", _elegido[1])).strip(" ,;.-")
        # El PDF arrastra el nombre del capítulo delante de la primera práctica de
        # cada sección ("Anestesiología anestesia mínima…"): se quita.
        _capnom = PMO_CAP.get(_code[:2])
        if _capnom and len(_letras(_nuevo)) > len(_letras(_capnom)):
            _m = re.match(r"\s*" + re.escape(_capnom) + r"\b[\s,:;.-]*(.+)$", _nuevo, re.I)
            if _m:
                _nuevo = _m.group(1).strip(" ,;.-")
        # El título del PDF viene acentuado y el del Único no. Si el elegido es un
        # recorte del actual, se recorta el actual para no perder las tildes.
        _la, _ln = _letras(_r["nombre"]), _letras(_nuevo)
        if _ln and _la.startswith(_ln):
            _acum, _corte = 0, len(_r["nombre"])
            for _i, _ch in enumerate(_r["nombre"]):
                if _acum == len(_ln):
                    _corte = _i
                    break
                if re.match(r"[A-Za-z]", _sinac(_ch)):
                    _acum += 1
            _nuevo = _r["nombre"][:_corte].strip(" ,;.-")
        # Red de seguridad: ninguna denominación del nomenclador es tan larga. Si el
        # candidato se desbordó, se conserva el título que ya había.
        if len(_nuevo) > 160 and len(_r["nombre"]) < len(_nuevo):
            _nuevo = ""
        # Si sólo cambian tildes o mayúsculas, se conserva el título actual.
        if _nuevo and _letras(_nuevo) != _la:
            # Un recorte mucho más corto que la denominación del Único suele ser un
            # corte de más: se marca para que lo revise un auditor.
            _u = _uni_por_codigo.get(_code, "")
            if _u and len(_letras(_u)) > 2 * len(_letras(_nuevo)):
                # El recorte se quedó corto: la denominación del Único cubre tanto el
                # arranque del PMO como el texto del OCR, así que se usa esa y se deja
                # marcado para que lo confirme un auditor.
                _nuevo = clean_pmo_name(_RE_COB.sub("", _u)).strip(" ,;.-") or _nuevo
                _elegido = ("unico", _nuevo)
                _r["titulo_revisar"] = True
                oft_rev += 1
            _r["nombre"] = _nuevo
            _r["titulo_origen"] = _elegido[0]
            oft_fix += 1
print(f"Nacional: títulos recompuestos {oft_fix} · con lateralidad {oft_lat} · a revisar {oft_rev}",
      file=sys.stderr)

# ---------- Oftalmología: equivalencias Único ↔ Nacional ----------
# Varias equivalencias de la planilla apuntan a códigos que no existen en el
# Nomenclador Nacional cargado (300113 «retinofluoresceinografía» remitía a 300153,
# inexistente). Cuando el destino no existe se vuelve a resolver: primero por código
# idéntico y, si no, por proximidad de nombre dentro del mismo capítulo.
_pmo_por_codigo = {r["code"]: k for k, r in records.items()
                   if r.get("nomenclador") == "PMO"}
_pmo_por_cap = defaultdict(list)
for _pc, _pk in _pmo_por_codigo.items():
    _pmo_por_cap[_pc[:2]].append(_pk)
eq_cod = eq_nom = eq_sin = 0
for _k, _r in records.items():
    if _r.get("nomenclador") != "UNICO":
        continue
    _eq = _r.get("equivalencia")
    if not _eq or _eq.get("key"):
        continue                      # sin equivalencia o ya resuelta
    # El código propio del Único (sin su prefijo de 2 dígitos) es la mejor pista.
    _propio = _r["code"][2:] if len(_r["code"]) == 8 else _r["code"]
    _nuevo_key = None
    _via = None
    if _propio in _pmo_por_codigo:    # 1) mismo número de código
        _nuevo_key = _pmo_por_codigo[_propio]
        _via = "codigo"
    else:                             # 2) proximidad de nombre dentro del capítulo
        _cap = cap_prefijo(_r["code"])
        _mejor, _mscore = None, 0.0
        for _pk in _pmo_por_cap.get(_cap, ()):
            _s = _dl.SequenceMatcher(None, _letras(_r["nombre"]),
                                     _letras(records[_pk]["nombre"]), autojunk=False).ratio()
            if _s > _mscore:
                _mejor, _mscore = _pk, _s
        # Umbral alto a propósito: por debajo aparecen falsos positivos que en
        # facturación son graves ("Centellograma de cerebro" contra "…de bazo" da
        # 0,83; "eco doppler obstétrico" contra "…periférico", 0,80).
        if _mejor and _mscore >= 0.88:
            _nuevo_key, _via = _mejor, "nombre"
    if not _nuevo_key:
        _eq["destino_inexistente"] = True
        eq_sin += 1
        continue
    _pr = records[_nuevo_key]
    _eq.update({"code": _pr["code"], "key": _nuevo_key, "desc": _pr["nombre"],
                "recalculada": _via})
    _r["auditoria"] = [a for a in (_r.get("auditoria") or [])
                       if not a.startswith("Equivale a la práctica")]
    _r["auditoria"].insert(0, "Equivale a la práctica " + _pr["code"] +
                           " del Nomenclador de Prestaciones Médicas.")
    annot_unico(_nuevo_key, _r["code"], _r["nombre"], None, _r.get("unico_tipo") or "med")
    if _via == "codigo":
        eq_cod += 1
    else:
        eq_nom += 1
print(f"Equivalencias re-resueltas: por código {eq_cod} · por nombre {eq_nom} · sin destino {eq_sin}",
      file=sys.stderr)

# la lateralidad del Nacional vale para la misma práctica en el Único
_lat_prop = 0
for _k, _r in records.items():
    if _r.get("nomenclador") != "UNICO" or _r.get("lateralidad"):
        continue
    _tgt = (_r.get("equivalencia") or {}).get("key")
    if _tgt and records.get(_tgt, {}).get("lateralidad"):
        _r["lateralidad"] = records[_tgt]["lateralidad"]
        _lat_prop += 1
print(f"Lateralidad propagada al Único: {_lat_prop}", file=sys.stderr)

# ---------- Lateralidad relevada por auditoría (tiene prioridad) ----------
# El OCR sólo la trae donde el PDF la imprime; el área de auditoría de VISITAR relevó
# además las que faltaban. Ese dato es de la casa, no inferido, así que pisa al del
# OCR y se aplica al código en todos los nomencladores donde aparezca.
try:
    LAT_CURADA = json.load(open("data/lateralidad_curada.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        LAT_CURADA = json.load(open("lateralidad_curada.json", encoding="utf-8"))
    except FileNotFoundError:
        LAT_CURADA = {"codigos": {}}
_LAT_MAP = LAT_CURADA.get("codigos", {})
lat_cur = lat_pisa = 0
for _k, _r in records.items():
    _val = _LAT_MAP.get(_r["code"])
    if not _val:
        continue
    if _r.get("lateralidad") and _r["lateralidad"] != _val:
        lat_pisa += 1
    _r["lateralidad"] = _val
    _r["lateralidad_origen"] = "auditoria"
    lat_cur += 1
print(f"Lateralidad relevada por auditoría: {lat_cur} fichas ({len(_LAT_MAP)} códigos) · "
      f"corrige al OCR en {lat_pisa}", file=sys.stderr)

# topes por capítulo (áreas con límite de cantidad de sesiones/visitas)
TOPES_CAP = {
    "33": "Salud mental: atención ambulatoria hasta 30 visitas por año calendario, sin exceder 4 consultas mensuales (Res. 201/02, Anexo I, punto 4).",
    "25": "Rehabilitación: Kinesioterapia y Fonoaudiología hasta 25 sesiones por beneficiario por año calendario cada una (Res. 201/02, Anexo I, punto 5).",
}
for _code, _r in records.items():
    if _r.get("nomenclador") == "PMO":
        _t = TOPES_CAP.get(_code[:2])
        if _t:
            _r["tope_pmo"] = _t
# propagar cobertura/tope al Único por equivalencia
for _k, _r in records.items():
    if _r.get("nomenclador") == "UNICO":
        _tgt = (_r.get("equivalencia") or {}).get("key")
        if _tgt and _tgt in records:
            _s = records[_tgt]
            if _s.get("cobertura_pmo") and "cobertura_pmo" not in _r:
                _r["cobertura_pmo"] = _s["cobertura_pmo"]
                if _s.get("cobertura_tipo"):
                    _r["cobertura_tipo"] = _s["cobertura_tipo"]
                # La planilla del Único traía sólo el encabezado («OBLIGACION de
                # cobertura en los siguientes casos:») sin los casos. Ahora que llega
                # el texto completo, ese resto suelto sobra.
                _obs = _r.get("observacion_unico") or ""
                if re.match(r"\s*(obligaci[oó]n\s+de\s+cobertura|se\s+asegura\s+la\s+cobertura)", _obs, re.I) \
                        and len(_obs) < 70:
                    _r.pop("observacion_unico", None)
            if _s.get("tope_pmo") and "tope_pmo" not in _r:
                _r["tope_pmo"] = _s["tope_pmo"]
print(f"PMO cobertura: títulos corregidos {pmo_fix} · con cobertura {pmo_cob} · generalidades {len(PMOCOB.get('generalidades',[]))} · topes {len(PMOCOB.get('topes',[]))}", file=sys.stderr)

# ---------- abreviaturas médicas: diccionario + vínculo a prácticas coincidentes ----------
import unicodedata as _ud
def _norm(s):
    return _ud.normalize("NFD", (s or "")).encode("ascii", "ignore").decode().lower()
try:
    ABREVS = json.load(open("data/abreviaturas.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        ABREVS = json.load(open("abreviaturas.json", encoding="utf-8"))
    except FileNotFoundError:
        ABREVS = []
# dedup: misma sigla + mismo significado (ignorando mayúsculas, acentos y
# conectores como "e/y/de/la"). Ej.: ABDI "ABDOMEN BLANDO DEPRESIBLE E INDOLORO"
# (HIBA) y "Abdomen blando depresible indoloro" (INSN) → una sola entrada.
_STOP = {"e","y","de","del","la","el","los","las","con","a","o","en","al","un","una","the"}
def _sigkey(s):
    s = _ud.normalize("NFD", (s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(t for t in s.split() if t not in _STOP)
_seen_ab = {}
_dedup = []
for _e in ABREVS:
    _dk = (_e["abrev"].upper(), _sigkey(_e["sig"]))
    if _dk in _seen_ab:
        # conservar la variante más descriptiva (más larga) y anexar la fuente
        _prev = _seen_ab[_dk]
        if len(_e["sig"]) > len(_prev["sig"]):
            _prev["sig"] = _e["sig"]
        _fs = {x.strip() for x in _prev.get("fuente", "").split("+") if x.strip()}
        _fs.add(_e.get("fuente", ""))
        _prev["fuente"] = " + ".join(sorted(f for f in _fs if f))
        continue
    _seen_ab[_dk] = _e
    _dedup.append(_e)
_dups_removed = len(ABREVS) - len(_dedup)
ABREVS = _dedup
_sig_by_word = defaultdict(list)
for _e in ABREVS:
    _s = _norm(_e["sig"])
    if len(_s) < 6:
        continue
    _w0 = next((w for w in _s.split() if len(w) >= 4), None)
    if _w0:
        _sig_by_word[_w0].append((_s, _e["abrev"]))
_abr_n = 0
for _k, _r in records.items():
    _name = _norm(_r["nombre"])
    _found = []
    for _w in set(w for w in _name.split() if len(w) >= 4):
        for _s, _ab in _sig_by_word.get(_w, []):
            if _s in _name and _ab not in _found:
                _found.append(_ab)
    if _found:
        _r["abrev_posibles"] = _found[:6]; _abr_n += 1
print(f"abreviaturas: {len(ABREVS)} (dup. eliminados {_dups_removed}) · prácticas con abreviatura sugerida {_abr_n}", file=sys.stderr)

# ---------- relaciones inversas por código: CIE-10 y normativa (en TODOS los nomencladores) ----------
code2cie = defaultdict(list)
for _cie, _keys in CIE10.get("relaciones", {}).items():
    for _k in _keys:
        if _cie not in code2cie[_k]:
            code2cie[_k].append(_cie)
code2ley = defaultdict(list)
for _l in leyes:
    for _c in _l.get("codigos", []):
        if _l["ley"] not in code2ley[_c]:
            code2ley[_c].append(_l["ley"])
# propagar por equivalencia: el código del Único hereda las relaciones de su equivalente (NBU/PMO)
for _k, _r in list(records.items()):
    if _r.get("nomenclador") == "UNICO":
        _tgt = (_r.get("equivalencia") or {}).get("key")
        if _tgt:
            for _c in code2cie.get(_tgt, []):
                if _c not in code2cie[_k]:
                    code2cie[_k].append(_c)
            for _c in code2ley.get(_tgt, []):
                if _c not in code2ley[_k]:
                    code2ley[_k].append(_c)
_cie_n = _ley_n = 0
for _k, _r in records.items():
    if code2cie.get(_k):
        _r["cie_rel"] = code2cie[_k][:12]; _cie_n += 1
    if code2ley.get(_k):
        _r["leyes_rel"] = code2ley[_k]; _ley_n += 1
print(f"relaciones inversas: {_cie_n} códigos con CIE-10 · {_ley_n} códigos con normativa", file=sys.stderr)

# ---------- SURGE — Sistema Único de Reintegro por Gestión de Enfermedades ----------
try:
    SURGE = json.load(open("data/surge.json", encoding="utf-8"))
except FileNotFoundError:
    try: SURGE = json.load(open("surge.json", encoding="utf-8"))
    except FileNotFoundError: SURGE = {"patologias": [], "codigo_patologia": {}}
# índice bare-code -> clave real del registro (NBU usa el código; Único usa "U"+código)
_code_key = {}
for _k, _r in records.items():
    _code_key.setdefault(str(_r.get("code")), _k)
_pat_by_id = {p["id"]: p for p in SURGE.get("patologias", [])}
# resolver los códigos de cada patología a claves reales y etiquetar cada práctica
for _p in SURGE.get("patologias", []):
    _p["codigos"] = [_code_key[c] for c in _p.get("codigos", []) if c in _code_key]
# grafo de equivalencias entre nomencladores (Único <-> Prestaciones/Laboratorio),
# no dirigido y transitivo, para propagar el vínculo SURGE a TODAS las representaciones
# del mismo código (ej.: PMO 070208 <-> Único U070208 <-> Único U40070208).
from collections import deque as _deque
_adj = defaultdict(set)
def _link(a, b):
    if a in records and b in records and a != b:
        _adj[a].add(b); _adj[b].add(a)
for _k, _r in records.items():
    _eq = _r.get("equivalencia")
    if isinstance(_eq, dict):
        _link(_k, _eq.get("key"))
    for _it in (_r.get("equivalencia_unico") or []):
        _link(_k, _it.get("unico_key"))

_surge_n = 0; _prop_n = 0
for _code, _pid in SURGE.get("codigo_patologia", {}).items():
    _origin = _code_key.get(_code); _pat = _pat_by_id.get(_pid)
    if not _origin or not _pat: continue
    _info = {
        "patologia_id": _pid, "patologia": _pat["nombre"], "especialidad": _pat["especialidad"],
        "requerimiento": _pat["requerimiento"], "medicacion": _pat.get("medicacion", []),
    }
    # recorrer el componente conexo de equivalencias y etiquetar todo lo alcanzable
    _seen = {_origin}; _q = _deque([_origin])
    while _q:
        _cur = _q.popleft()
        if "surge" not in records[_cur]:
            records[_cur]["surge"] = _info
            if _cur == _origin: _surge_n += 1
            else: _prop_n += 1
            if _cur not in _pat["codigos"]: _pat["codigos"].append(_cur)
        for _nb in _adj[_cur]:
            if _nb not in _seen: _seen.add(_nb); _q.append(_nb)
print(f"SURGE: patologías {len(SURGE.get('patologias', []))} · códigos (SUR)/(SURGE) {_surge_n} · propagados por equivalencia {_prop_n}", file=sys.stderr)

# grupo stats
grupos_stats = defaultdict(int)
nomen_stats = defaultdict(int)
for rec in records.values():
    grupos_stats[rec["grupo"]] += 1
    nomen_stats[rec["nomenclador"]] += 1

db = {
    "meta": {
        "titulo": "Manual Inteligente Unificado de Códigos Médicos",
        "fuente": "NBU — Nomenclador Bioquímico Único v2012/2016 (CUBRA) + Catálogo de Prestaciones del PMO (Res. 201/2002, S.S. Salud)",
        "overlay": "Anexo Enero 2024 (U.B. actualizadas) aplicado como valor_actualizado_2024 donde corresponde.",
        "total_codigos": len(records),
        "secciones": SECCION_LABEL,
        "nomencladores": {
            "NBU": "NBU — Nomenclador Bioquímico Único (bioquímica / laboratorio)",
            "PMO": "Catálogo de Prestaciones del PMO (prestaciones médicas y quirúrgicas)",
            "ODO": "Nomenclador Nacional — Prácticas Odontológicas",
            "UNICO": "Nomenclador ÚNICO (VISITAR SRL) — en elaboración, con equivalencias a Prestaciones Médicas",
        },
        "nomenclador_counts": dict(nomen_stats),
        "unico_sin_equivalencia": sin_equiv + extra_sin,
        "pmo_capitulos": PMO_CAP,
        "pmo_normas_capitulo": CHAPTER_NORMS,
        "pmo_normas_nota": "Normas generales orientativas de facturación por capítulo. Verificar siempre contra la norma/convenio aplicable. No reemplazan al texto oficial del nomenclador.",
        "pmo_generalidades": PMOCOB.get("generalidades", []),
        "pmo_topes": PMOCOB.get("topes", []),
        "pmo_asociaciones": {},
        "grupos": dict(sorted(grupos_stats.items(), key=lambda x: -x[1])),
        "nota_grupos": "El 'grupo/especialidad' es orientativo para navegar. En el NBU la clasificación oficial es la sección (PMO/PE/Gestión); en el Catálogo PMO, el capítulo/especialidad proviene del código.",
    },
    "glosario": glossary,
    "leyes": leyes,
    "cie10": CIE10,
    "abreviaturas": ABREVS,
    "surge": SURGE,
    "codigos": records,
}

# ---------- correcciones de contenido hechas por auditoría ----------
# Se aplican al final y pisan todo lo anterior: las hizo una persona que sabe, sobre
# fichas que el pipeline no pudo resolver solo. Salen del panel de administración de
# la app, con «Exportar correcciones para la base».
try:
    CORR = json.load(open("data/correcciones_curadas.json", encoding="utf-8"))
except FileNotFoundError:
    try:
        CORR = json.load(open("correcciones_curadas.json", encoding="utf-8"))
    except FileNotFoundError:
        CORR = {"codigos": {}}
corr_n = 0
for _code, _ov in (CORR.get("codigos") or {}).items():
    _r = records.get(_code)
    if not _r:
        print(f"  aviso: corrección para {_code}, que no está en la base", file=sys.stderr)
        continue
    if _ov.get("nombre"):
        _r["nombre"] = _ov["nombre"]
        # corregido a mano: ya no hay nada que confirmar
        _r.pop("titulo_revisar", None)
        _r.pop("sin_denominacion", None)
        _r.pop("titulo_origen", None)
    if "norma" in _ov:
        _r["norma"] = _ov["norma"]
    if "auditoria" in _ov:
        _r["auditoria"] = _ov["auditoria"]
    if _ov.get("asoc_extra"):
        _r["asoc_extra"] = _ov["asoc_extra"]
    _r["correccion_curada"] = True
    corr_n += 1
if corr_n:
    print(f"Correcciones de auditoría aplicadas: {corr_n}", file=sys.stderr)

# ---------- guarda final: ninguna ficha sin denominación ----------
# Alguna prestación llega con el título destruido en la fuente (p. ej. 130303, que
# el OCR del PDF dejó ilegible). No se inventa una denominación: se marca la ficha
# como sin denominación en origen para que se vea el faltante y pueda corregirse
# desde el panel de administración.
_sin_denom = 0
for _k, _r in records.items():
    if not (_r.get("nombre") or "").strip():
        _r["nombre"] = f"[{_r['code']}] — sin denominación en la fuente"
        _r["sin_denominacion"] = True
        _sin_denom += 1
if _sin_denom:
    print(f"fichas sin denominación en la fuente: {_sin_denom}", file=sys.stderr)

json.dump(db, open("nbu_db.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"CIE-10: {len(CIE10.get('codigos', {}))} diagnósticos · {len(CIE10.get('relaciones', {}))} con prácticas relacionadas", file=sys.stderr)

# report
print(f"codigos: {len(records)}", file=sys.stderr)
print(f"con norma: {sum(1 for r in records.values() if r['norma'])}", file=sys.stderr)
print(f"con relaciones: {sum(1 for r in records.values() if any(r['relaciones'].values()))}", file=sys.stderr)
print(f"con overlay 2024: {sum(1 for r in records.values() if 'ub_actualizado_2024' in r['valor'])}", file=sys.stderr)
print("grupos:", file=sys.stderr)
for g, c in sorted(grupos_stats.items(), key=lambda x: -x[1]):
    print(f"  {c:4d}  {g}", file=sys.stderr)
