"""Lee NORMAS ESPECÍFICAS e INTERPRETACIONES del NBU (CUBRA) desde el PDF.

La página es una tabla de tres columnas: PRÁCTICA (con el código) · NORMA
MÍNIMA DE TRABAJO · INTERPRETACIÓN. Leerla como texto corrido entrelaza las
tres, y agrupar por renglones falla porque una celda alta ocupa varias líneas
mientras la de al lado ocupa una.

Por eso cada fila se ancla en la POSICIÓN DEL CÓDIGO: todo lo que está por
debajo de un código y por encima del siguiente pertenece a esa fila, y la
columna se decide por la coordenada horizontal. Es como está armada la tabla.
"""
import pdfplumber, re

C1, C2 = 196, 367          # límites de las tres columnas, medidos sobre el PDF
COD = re.compile(r'^6\d{5}$')
BASURA = re.compile(r'^(Página\s+\d+.*|CUBRA\s*-.*|.*-\s*Página\s+\d+|CTP\s*-\s*NBU.*|'
                    r'UNICO\s+Versión.*|NORMAS ESPEC.*|NBU\s*-\s*P\.M\.O.*|'
                    r'Actualización\s+\d+|El Ítem asignado.*|y referente al C.*|'
                    r'PRACTICA|ITEM|BIOQUÍMICA)$', re.I)

def _texto(ws):
    """Ordena palabras y las une respetando renglones."""
    ws = sorted(ws, key=lambda w: (round(w['top']/2), w['x0']))
    out, cur, ct = [], [], None
    for w in ws:
        if ct is not None and abs(w['top']-ct) > 2:
            out.append(' '.join(cur)); cur=[]
        cur.append(w['text']); ct=w['top']
    if cur: out.append(' '.join(cur))
    out = [l for l in out if not BASURA.match(l.strip())]
    s = ''
    for l in out:
        l=l.strip()
        if not l: continue
        if s.endswith('-') and not s.endswith(' -'): s = s[:-1]+l   # palabra partida
        elif s: s += ' '+l
        else: s = l
    return re.sub(r'\s+',' ',s).strip()

def parse(archivo):
    filas=[]
    with pdfplumber.open(archivo) as pdf:
        for pg in pdf.pages:
            ws = pg.extract_words(use_text_flow=False)
            # Anclas: los códigos de la primera columna, en orden vertical.
            anclas = sorted([w for w in ws if COD.fullmatch(w['text']) and w['x0'] < 100],
                            key=lambda w: w['top'])
            if not anclas: continue
            for i, a in enumerate(anclas):
                arriba = a['top'] - 2
                abajo  = anclas[i+1]['top'] - 2 if i+1 < len(anclas) else 10**6
                dentro = [w for w in ws if arriba <= w['top'] < abajo and w is not a]
                filas.append({
                    'codigo':   a['text'],
                    'practica': _texto([w for w in dentro if w['x0'] < C1]),
                    'norma':    _texto([w for w in dentro if C1 <= w['x0'] < C2]),
                    'interp':   _texto([w for w in dentro if w['x0'] >= C2]),
                })
    return filas
