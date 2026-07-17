#!/usr/bin/env python3
"""Parse cached OCR of the dental (odontología) Nomenclador into per-code values, checksum-validated."""
import json, re, sys
from collections import defaultdict

B = {
    "code":  (0.00, 0.13),
    "name":  (0.13, 0.53),
    "hon":   (0.575, 0.655),
    "gas":   (0.688, 0.748),
    "valor": (0.748, 0.792),
    "cose":  (0.792, 0.865),
}
CODE_RE = re.compile(r"^(\d{2})\.(\d{2})(?:[.:](\d{2}))?\.?([A-Z])?$")
CHAP_RE = re.compile(r"^(\d{2})$")

def to_num(t):
    t = re.sub(r"[^0-9.]", "", t.replace(",", "."))
    if t.count(".") > 1:
        p = t.split("."); t = "".join(p[:-1]) + "." + p[-1]
    try:
        return float(t)
    except ValueError:
        return None

def col_of(xc, w):
    f = xc / w
    for name, (a, b) in B.items():
        if a <= f < b:
            return name
    return None

CAPS = {}

def parse_page(pg):
    w = pg["w"]; toks = pg["toks"]
    # chapter headers: 2-digit code at far left with a title
    for x0, y0, x1, y1, t, c in toks:
        m = CHAP_RE.match(t.strip())
        if m and (x0/w) < 0.13:
            title = " ".join(z[4] for z in toks if abs(z[1]-y0) < 18 and 0.2 < ((z[0]+z[2])/2)/w < 0.75 and not CHAP_RE.match(z[4].strip()))
            title = re.sub(r"\s+", " ", title).strip()
            if 3 < len(title) < 45 and m.group(1) not in CAPS:
                CAPS[m.group(1)] = title.title()
    codes = []
    for x0, y0, x1, y1, t, c in toks:
        m = CODE_RE.match(t.strip())
        if m and (x0/w) < 0.13:
            cid = m.group(1) + m.group(2) + (m.group(3) or "") + (m.group(4) or "")
            codes.append((y0, cid, m.group(1)))
    codes.sort()
    if not codes:
        return {}
    tops = [z[0] for z in codes]
    lo = [(-1e9 if i == 0 else (tops[i-1]+tops[i])/2) for i in range(len(codes))]
    hi = [(1e9 if i == len(codes)-1 else (tops[i]+tops[i+1])/2) for i in range(len(codes))]
    out = {}
    for i, (cy, cid, chap) in enumerate(codes):
        band = [z for z in toks if lo[i] <= z[1] < hi[i]]
        cols = defaultdict(list)
        for x0, y0, x1, y1, t, c in band:
            col = col_of((x0+x1)/2, w)
            if col:
                cols[col].append((y0, t))
        nt = sorted(cols.get("name", []), key=lambda z: (round(z[0]/12), z[0]))
        name = re.sub(r"\s+", " ", " ".join(z[1] for z in nt)).strip()
        def uv(col):
            vals = [(y, to_num(t)) for y, t in cols.get(col, []) if to_num(t) is not None]
            uu = pp = None
            for y, v in vals:
                if y < cy:
                    uu = v if uu is None else uu
                else:
                    pp = v if pp is None else pp
            if uu is None and pp is None and vals:
                pp = vals[0][1]
            return uu, pp
        hon_u, hon_p = uv("hon")
        gas_u, gas_p = uv("gas")
        def one(col):
            vs = [to_num(t) for y, t in cols.get(col, []) if to_num(t) is not None]
            return vs[0] if vs else None
        valor = one("valor")
        cose = one("cose")
        priced = (hon_u is not None) or (hon_p is not None) or (valor is not None)
        chk = None
        if valor is not None and (hon_p is not None or gas_p is not None):
            s = (hon_p or 0) + (gas_p or 0)
            chk = abs(s - valor) <= max(0.15, valor*0.03)
        out[cid] = {
            "codigo": codes[i][1], "dotted": re.sub(r"(\d\d)(\d\d)([A-Z0-9]?)", r"\1.\2\3", cid),
            "nombre_ocr": name, "page": pg["page"], "capitulo_num": chap,
            "honorarios": {"u": hon_u, "p": hon_p}, "gastos": {"u": gas_u, "p": gas_p},
            "valor_practica": valor, "coseguro": cose, "checksum_ok": chk,
            "tipo": "priced" if priced else "modificador",
        }
    return out

def main():
    result = {}
    for f in sys.argv[1:]:
        for pg in json.load(open(f, encoding="utf-8")):
            result.update(parse_page(pg))
    for r in result.values():
        r["capitulo"] = CAPS.get(r["capitulo_num"], "")
    json.dump({"records": result, "capitulos": CAPS}, open("nn_odo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot = len(result)
    priced = [c for c, r in result.items() if r["tipo"] == "priced"]
    okc = [c for c, r in result.items() if r["checksum_ok"] is True]
    print(f"ODO codes: {tot} | priced: {len(priced)} | checksum OK: {len(okc)}", file=sys.stderr)
    print("capitulos:", CAPS, file=sys.stderr)
    for c in ["0101", "0201", "0202", "0301"]:
        if c in result:
            r = result[c]; print(f"  {c} {r['nombre_ocr'][:32]!r} hon$={r['honorarios']['p']} gas$={r['gastos']['p']} valor={r['valor_practica']} cose={r['coseguro']} chk={r['checksum_ok']}", file=sys.stderr)

if __name__ == "__main__":
    main()
