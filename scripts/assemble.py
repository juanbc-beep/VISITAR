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
    {"ley": "25326", "titulo": "Protección de Datos Personales", "sancion": "04/10/2000"},
    {"ley": "25543", "titulo": "Test HIV obligatorio a embarazadas", "sancion": "27/11/2001"},
    {"ley": "26279", "titulo": "Pesquisa Neonatal", "sancion": "08/08/2007"},
    {"ley": "26281", "titulo": "Prevención y Control del Chagas", "sancion": "08/08/2007"},
    {"ley": "26369", "titulo": "Detección de estreptococo Grupo B a embarazadas", "sancion": "16/04/2008"},
    {"ley": "26529", "titulo": "Derechos del Paciente", "sancion": "21/10/2009"},
    {"ley": "26588", "titulo": "Celiaquía", "sancion": "02/12/2009"},
    {"ley": "26862", "titulo": "Fertilización Asistida", "sancion": "05/06/2013"},
    {"ley": "27232", "titulo": "Ley NBU (aplicación obligatoria nacional)", "sancion": "26/11/2015"},
]

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
        },
        "nomenclador_counts": dict(nomen_stats),
        "pmo_capitulos": PMO_CAP,
        "pmo_normas_capitulo": CHAPTER_NORMS,
        "pmo_normas_nota": "Normas generales orientativas de facturación por capítulo. Verificar siempre contra la norma/convenio aplicable. No reemplazan al texto oficial del nomenclador.",
        "pmo_asociaciones": {},
        "grupos": dict(sorted(grupos_stats.items(), key=lambda x: -x[1])),
        "nota_grupos": "El 'grupo/especialidad' es orientativo para navegar. En el NBU la clasificación oficial es la sección (PMO/PE/Gestión); en el Catálogo PMO, el capítulo/especialidad proviene del código.",
    },
    "glosario": glossary,
    "leyes": leyes,
    "codigos": records,
}
json.dump(db, open("nbu_db.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# report
print(f"codigos: {len(records)}", file=sys.stderr)
print(f"con norma: {sum(1 for r in records.values() if r['norma'])}", file=sys.stderr)
print(f"con relaciones: {sum(1 for r in records.values() if any(r['relaciones'].values()))}", file=sys.stderr)
print(f"con overlay 2024: {sum(1 for r in records.values() if 'ub_actualizado_2024' in r['valor'])}", file=sys.stderr)
print("grupos:", file=sys.stderr)
for g, c in sorted(grupos_stats.items(), key=lambda x: -x[1]):
    print(f"  {c:4d}  {g}", file=sys.stderr)
