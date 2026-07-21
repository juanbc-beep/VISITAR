#!/usr/bin/env python3
"""Re-parse the PMO (Res. 201/2002) with column-aware extraction:
- ANEXO II: código de 6 dígitos -> {titulo limpio, cobertura (obligación/notas)}
- ANEXO I: generalidades por sección + topes (sesiones/visitas/edad)."""
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
# clasificar páginas por anexo
anexo_of = {}
cur = 0
for pi in range(len(pdf.pages)):
    t = pdf.pages[pi].extract_text() or ""
    for a,mark in [(1,'ANEXO I'),(2,'ANEXO II'),(3,'ANEXO III'),(4,'ANEXO IV')]:
        if re.search(r'ANEXO %s\b' % {1:'I',2:'II',3:'III',4:'IV'}[a], t):
            cur = max(cur, a)
    anexo_of[pi] = cur

CODE = re.compile(r'^(\d{6})\s+(.+)$')
def is_cont(l):
    return l and not CODE.match(l) and (l[0].islower() or l[0] in '(,')

# ---- ANEXO II: códigos ----
codigos = {}
lines2 = []
for pi in range(len(pdf.pages)):
    if anexo_of[pi] == 2:
        lines2 += col_lines(pdf.pages[pi])
i = 0
while i < len(lines2):
    ln = lines2[i].strip()
    m = CODE.match(ln)
    if m:
        code = m.group(1); title = m.group(2).strip()
        j = i+1
        # continuación del título (línea que empieza en minúscula)
        while j < len(lines2) and is_cont(lines2[j].strip()) and not lines2[j].strip().startswith('•'):
            title += ' ' + lines2[j].strip(); j += 1
        # cobertura: líneas hasta el próximo código
        cob = []
        while j < len(lines2) and not CODE.match(lines2[j].strip()):
            s = lines2[j].strip()
            if s: cob.append(s)
            j += 1
        title = re.sub(r'\s+', ' ', title).strip(' .')
        cobertura = re.sub(r'\s+', ' ', ' '.join(cob)).strip()
        # limpiar viñeta inicial
        cobertura = re.sub(r'^•\s*', '', cobertura)
        if code not in codigos or len(title) < len(codigos[code]['titulo']):
            codigos[code] = {"titulo": title, "cobertura": cobertura if len(cobertura) > 8 else ""}
        i = j
    else:
        i += 1

# ---- ANEXO I: generalidades + topes ----
lines1 = []
for pi in range(len(pdf.pages)):
    if anexo_of[pi] == 1:
        lines1 += col_lines(pdf.pages[pi])
blob = "\n".join(lines1)
blob = re.sub(r'-\n', '', blob)          # unir palabras cortadas por guión
blob = re.sub(r'\n', ' ', blob)
blob = re.sub(r'\s+', ' ', blob)
# secciones de nivel 1: "N. Título:" (N 1..9)
SEC = re.compile(r'(?:^|\s)(\d)\.?\s+([A-ZÁÉÍÓÚ][^:]{3,40}):')
gener = []
marks = list(SEC.finditer(blob))
for idx, mm in enumerate(marks):
    num = mm.group(1); titulo = mm.group(2).strip()
    start = mm.end()
    end = marks[idx+1].start() if idx+1 < len(marks) else len(blob)
    texto = blob[start:end].strip()
    if 3 < len(texto):
        gener.append({"num": num, "titulo": titulo, "texto": texto[:1400]})

# topes: frases con "hasta N ... (sesiones|visitas|consultas|año|años|veces)"
topes = []
for m in re.finditer(r'([^.]{0,90}?hasta (?:los )?\d+[^.]{0,90}(?:sesiones|visitas|consultas|año|años|veces|meses)[^.]{0,40})', blob):
    s = re.sub(r'\s+', ' ', m.group(1)).strip()
    if len(s) > 12: topes.append(s)

json.dump({"codigos": codigos, "generalidades": gener, "topes": topes},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"PMO: códigos {len(codigos)} · con cobertura {sum(1 for v in codigos.values() if v['cobertura'])} · generalidades {len(gener)} · topes {len(topes)}", file=sys.stderr)
for c in ["342014","342013","250102"]:
    if c in codigos: print("  ", c, "->", codigos[c]["titulo"][:45], "| cob:", codigos[c]["cobertura"][:50], file=sys.stderr)
