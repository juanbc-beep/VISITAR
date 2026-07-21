#!/usr/bin/env python3
"""Parse medical abbreviation dictionaries into {abrev, sig} entries."""
import json, re, sys
import pdfplumber

OUT = "data/abreviaturas.json"
HIBA = sys.argv[1] if len(sys.argv) > 1 else None
RD = sys.argv[2] if len(sys.argv) > 2 else None

def col_lines(pg):
    w=pg.width; mid=w/2; words=pg.extract_words(use_text_flow=False)
    def lines(ws):
        ws=sorted(ws,key=lambda z:(round(z['top']/3),z['x0']));out=[];cur=[];ct=None
        for z in ws:
            if ct is None or abs(z['top']-ct)<4:cur.append(z['text'])
            else:out.append(' '.join(cur));cur=[z['text']]
            ct=z['top']
        if cur:out.append(' '.join(cur))
        return out
    return lines([x for x in words if (x['x0']+x['x1'])/2<mid])+lines([x for x in words if (x['x0']+x['x1'])/2>=mid])

entries = {}
def add(ab, sig, fuente):
    ab=ab.strip(' :.-'); sig=re.sub(r'\s+',' ',sig).strip(' .')
    if not ab or len(ab)>18 or len(sig)<2 or len(sig)>90: return
    if re.search(r'(BUSCAR|presione|aparecer|escriba|CATÁLOGO|INSTITUTO|abreviatura en la)', sig, re.I): return
    key=(ab.upper(), sig.lower())
    if key not in entries:
        entries[key]={"abrev":ab,"sig":sig,"fuente":fuente}

# HIBA: ABREV SIGNIFICADO (mayús) Permitida/…
if HIBA:
    ST=re.compile(r'^(\S+)\s+(.+?)\s+(Permitida|No permitida|Prohibida|No recomendada|Desaconsejada)\s*$')
    for pg in pdfplumber.open(HIBA).pages:
        for ln in (pg.extract_text() or '').split('\n'):
            m=ST.match(ln.strip())
            if m: add(m.group(1), m.group(2), "HIBA")

# RD-103: ABREV: significado.  (2 columnas)
if RD:
    RE=re.compile(r'^([A-Za-zÁÉÍÓÚÑ°/][\w/°ÁÉÍÓÚÑ.\-]{0,17}):\s+(.+)$')
    for pg in pdfplumber.open(RD).pages:
        for ln in col_lines(pg):
            m=RE.match(ln.strip())
            if m: add(m.group(1), m.group(2), "INSN")

out=sorted(entries.values(), key=lambda e:e["abrev"].upper())
json.dump(out, open(OUT,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"abreviaturas: {len(out)}", file=sys.stderr)
for e in out[:6]: print("  ",e["abrev"],"=",e["sig"], file=sys.stderr)
