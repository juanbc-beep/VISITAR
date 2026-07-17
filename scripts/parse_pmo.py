#!/usr/bin/env python3
"""Parse the PMO 'Catálogo de Prestaciones' (2-column medical/surgical nomenclador)."""
import pdfplumber, re, json, sys
PDF = "/root/.claude/uploads/ac5e0c28-47d1-5f23-85ef-4bdfc9a090ce/960a807d-PMO_PAG_25.pdf"
CODE = re.compile(r"^\d{6}$")
# columns: (code_x, name_left, right_bound)
COLS = [(70.8, 100, 305), (311.8, 341, 560)]

def clean(s):
    return re.sub(r"\s+", " ", s).strip()

def parse():
    pdf = pdfplumber.open(PDF)
    records = {}         # code -> {nombre, capitulo, page}
    order = []
    started = False
    current_cap = None
    for pi in range(len(pdf.pages)):
        words = pdf.pages[pi].extract_words(use_text_flow=False, keep_blank_chars=False)
        for cx, nx, rb in COLS:
            colw = [w for w in words if cx-4 <= w["x0"] < rb]
            # anchors in this column, sorted by top
            anchors = [w for w in colw if abs(w["x0"]-cx) < 4 and CODE.match(w["text"])]
            anchors.sort(key=lambda w: w["top"])
            if not anchors:
                continue
            # header candidates: non-code text starting at code-x
            headers = [w for w in colw if abs(w["x0"]-cx) < 6 and not CODE.match(w["text"]) and w["text"][:1].isalpha()]
            tops = [a["top"] for a in anchors]
            lo = [(-1e9 if i==0 else (tops[i-1]+tops[i])/2) for i in range(len(anchors))]
            hi = [(1e9 if i==len(anchors)-1 else (tops[i]+tops[i+1])/2) for i in range(len(anchors))]
            for i, a in enumerate(anchors):
                code = a["text"]
                if code == "010101":
                    started = True
                if not started:
                    continue
                # name tokens: in [nx, rb], within band, excluding the code itself
                band = [w for w in colw if lo[i] <= w["top"] < hi[i] and w["x0"] >= nx-2 and not (abs(w["x0"]-cx)<4 and CODE.match(w["text"]))]
                band.sort(key=lambda w: (round(w["top"]), w["x0"]))
                name = clean(" ".join(w["text"] for w in band))
                # section header: a header line just above this code (within ~14px), short, title-like
                hdr = [h for h in headers if a["top"]-16 < h["top"] < a["top"]-1]
                if hdr:
                    htop = min(h["top"] for h in hdr)
                    htoks = sorted([h for h in headers if abs(h["top"]-htop)<3], key=lambda w:w["x0"])
                    htext = clean(" ".join(h["text"] for h in htoks))
                    # accept as chapter title if short and not ending in prose punctuation
                    if 3 < len(htext) < 60 and not htext.endswith((".", ",")) and not re.search(r"\d", htext):
                        current_cap = htext
                if code not in records:
                    records[code] = {"nombre": name, "capitulo": current_cap, "prefix": code[:2], "page": pi+1}
                    order.append(code)
    return records, order

def main():
    records, order = parse()
    print(f"PMO codes: {len(records)}", file=sys.stderr)
    # chapter by prefix (take most common capitulo per prefix)
    from collections import Counter, defaultdict
    byprefix = defaultdict(Counter)
    for c, r in records.items():
        if r["capitulo"]:
            byprefix[r["prefix"]][r["capitulo"]] += 1
    prefix_cap = {p: cc.most_common(1)[0][0] for p, cc in byprefix.items()}
    print("prefix -> capitulo:", file=sys.stderr)
    for p in sorted(prefix_cap):
        print(f"  {p}: {prefix_cap[p]}  ({sum(1 for r in records.values() if r['prefix']==p)} códigos)", file=sys.stderr)
    noname = [c for c,r in records.items() if not r["nombre"]]
    print(f"sin nombre: {len(noname)} {noname[:10]}", file=sys.stderr)
    json.dump({"records": records, "order": order, "prefix_cap": prefix_cap},
              open("pmo_catalog.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
