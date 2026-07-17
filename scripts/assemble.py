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
    txt = None
    for path in ("nbu_reval.txt", "data/nbu_anexo2024.txt", "nbu_anexo2024.txt"):
        try:
            txt = open(path, encoding="utf-8").read(); break
        except FileNotFoundError:
            continue
    if txt is None:
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
    rec["auditoria"] = audit_tips(rec)
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
for rec in records.values():
    grupos_stats[rec["grupo"]] += 1

db = {
    "meta": {
        "titulo": "Manual Inteligente Unificado de Códigos Médicos",
        "fuente": "NBU — Nomenclador Bioquímico Único · Versión 2012 · Actualización 2016 (CUBRA)",
        "overlay": "Anexo Enero 2024 (U.B. actualizadas) aplicado como valor_actualizado_2024 donde corresponde.",
        "total_codigos": len(records),
        "secciones": SECCION_LABEL,
        "grupos": dict(sorted(grupos_stats.items(), key=lambda x: -x[1])),
        "nota_grupos": "El 'grupo/especialidad' es una clasificación orientativa para facilitar la navegación; el NBU es alfabético. La sección (PMO/PE/Gestión) es la clasificación oficial.",
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
