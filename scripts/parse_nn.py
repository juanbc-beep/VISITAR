#!/usr/bin/env python3
"""Parse cached OCR of the Nomenclador Nacional into per-code values, with checksum validation."""
import json, re, sys
from collections import defaultdict

# fractional x-bands (of page width) for each column
B = {
    "code":  (0.00, 0.12),
    "name":  (0.12, 0.52),
    "esp":   (0.545, 0.592),
    "ayum":  (0.592, 0.625),
    "ayuv":  (0.625, 0.672),
    "anes":  (0.672, 0.722),
    "gasto": (0.722, 0.778),
    "total": (0.778, 0.845),
}
CODE_RE = re.compile(r"^(\d{2})[.\-](\d{2})[.\-](\d{2})$")
GROUP_RE = re.compile(r"^(\d{2})[.\-](\d{2})$")
NUM_RE = re.compile(r"^\d{1,4}([.,]\d{1,2})?$")

def to_num(t):
    t = t.replace(",", ".").replace(" ", "")
    t = re.sub(r"[^0-9.]", "", t)
    if t.count(".") > 1:  # keep last as decimal
        parts = t.split("."); t = "".join(parts[:-1]) + "." + parts[-1]
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

def parse_page(pg):
    w = pg["w"]; toks = pg["toks"]
    codes = []
    groups = []
    for x0, y0, x1, y1, t, c in toks:
        tt = t.strip()
        m = CODE_RE.match(tt)
        if m and (x0 / w) < 0.12:
            codes.append((y0, "".join(m.groups()), c))
        mg = GROUP_RE.match(tt)
        if mg and (x0 / w) < 0.14:
            groups.append((y0, tt))
    codes.sort()
    if not codes:
        return {}, groups
    tops = [cy for cy, _, _ in codes]
    lo = [(-1e9 if i == 0 else (tops[i-1]+tops[i])/2) for i in range(len(codes))]
    hi = [(1e9 if i == len(codes)-1 else (tops[i]+tops[i+1])/2) for i in range(len(codes))]
    out = {}
    for i, (cy, code, cc) in enumerate(codes):
        band = [z for z in toks if lo[i] <= z[1] < hi[i]]
        cols = defaultdict(list)
        for x0, y0, x1, y1, t, c in band:
            xc = (x0 + x1) / 2
            col = col_of(xc, w)
            if col:
                cols[col].append((y0, t, c, x0))
        # name
        nt = sorted(cols.get("name", []), key=lambda z: (round(z[0]/12), z[3]))
        name = re.sub(r"\s+", " ", " ".join(z[1] for z in nt)).strip()
        # detect the two sub-row y-levels (U. galeno on top, $ pesos below) from the markers at x~0.52
        u_y = p_y = None
        for x0, y0, x1, y1, t, c in band:
            f = ((x0+x1)/2)/w
            if 0.5 <= f < 0.545:
                tt = t.strip()
                if "U" in tt.upper() and u_y is None: u_y = y0
                if "$" in tt or "S" == tt or tt in ("s", "$"):
                    if p_y is None: p_y = y0
        if u_y is None: u_y = cy - 15
        if p_y is None: p_y = cy + 15
        def uv(col):
            vals = [(y, to_num(t)) for y, t, c, x in cols.get(col, []) if to_num(t) is not None]
            uu = pp = None
            for y, v in vals:
                if abs(y-u_y) <= abs(y-p_y):
                    if uu is None or abs(y-u_y) < abs(uu[0]-u_y): uu = (y, v)
                else:
                    if pp is None or abs(y-p_y) < abs(pp[0]-p_y): pp = (y, v)
            return (uu[1] if uu else None), (pp[1] if pp else None)
        esp_u, esp_p = uv("esp")
        ayu_u, ayu_p = uv("ayuv")
        anes_u, anes_p = uv("anes")
        gas_u, gas_p = uv("gasto")
        # ayudante multiplier
        ayn = None
        for y, t, c, x in cols.get("ayum", []):
            mm = re.search(r"(\d+)\s*[xX]", t)
            if mm:
                ayn = int(mm.group(1))
        # total (single value nearest code y)
        tot = None
        tv = [(abs(y-cy), to_num(t)) for y, t, c, x in cols.get("total", []) if to_num(t) is not None]
        if tv:
            tot = sorted(tv)[0][1]
        # classify: a "priced" row must have an especialista honorario (galeno or $)
        priced = (esp_u is not None) or (esp_p is not None)
        if not priced:
            # special / added code without standard galeno pricing -> drop spurious values
            esp_u = esp_p = ayu_u = ayu_p = anes_u = anes_p = gas_u = gas_p = tot = None
        # checksum on pesos
        parts = [p for p in (esp_p, ayu_p, anes_p, gas_p) if p is not None]
        chk = None
        if tot is not None and esp_p is not None and gas_p is not None:
            chk = abs(sum(parts) - tot) <= max(0.6, tot*0.012)
        out[code] = {
            "tipo": "priced" if priced else "sin_valor",
            "nombre_ocr": name, "page": pg["page"],
            "esp": {"u": esp_u, "p": esp_p}, "ayu": {"n": ayn, "u": ayu_u, "p": ayu_p},
            "anes": {"u": anes_u, "p": anes_p}, "gasto": {"u": gas_u, "p": gas_p},
            "total_p": tot, "checksum_ok": chk,
        }
    return out, groups

def main():
    result = {}
    for f in sys.argv[1:]:
        pages = json.load(open(f, encoding="utf-8"))
        for pg in pages:
            recs, groups = parse_page(pg)
            result.update(recs)
    json.dump(result, open("nn_values.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot = len(result)
    withval = [c for c, r in result.items() if r["total_p"] is not None]
    chk_ok = [c for c, r in result.items() if r["checksum_ok"] is True]
    chk_bad = [c for c, r in result.items() if r["checksum_ok"] is False]
    print(f"NN codes: {tot} | con total: {len(withval)} | checksum OK: {len(chk_ok)} | checksum FAIL: {len(chk_bad)} | s/checksum: {tot-len(chk_ok)-len(chk_bad)}", file=sys.stderr)
    for c in ["080201","080202","080203","080204","080205","080206"]:
        if c in result:
            r=result[c]; print(f"  {c} {r['nombre_ocr'][:34]!r} esp$={r['esp']['p']} ayu={r['ayu']['n']}x/{r['ayu']['p']} anes$={r['anes']['p']} gasto$={r['gasto']['p']} total={r['total_p']} chk={r['checksum_ok']}", file=sys.stderr)

if __name__ == "__main__":
    main()
