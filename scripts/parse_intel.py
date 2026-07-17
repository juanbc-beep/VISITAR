#!/usr/bin/env python3
"""Parse NBU intelligence layers: sinonimias, abreviaturas, normas (with code relationships)."""
import pdfplumber, re, json, sys
from collections import defaultdict

PDF = "/root/.claude/uploads/ac5e0c28-47d1-5f23-85ef-4bdfc9a090ce/f839a468-NBUVersion2012Act.2016.pdf"
CODE_RE = re.compile(r"^66\d{4}$")
FOOTER_WORDS = {"CTP", "CUBRA"}

def bands(page, min_top=0, max_top=1e9):
    """Return list of (code, [words]) grouped by code anchor via vertical banding."""
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    header_tops = [w["top"] for w in words if w["text"] == "CÓDIGO"]
    def is_header(w):
        return any(abs(w["top"] - h) < 4 for h in header_tops)
    codes = [w for w in words if w["x0"] < 82 and CODE_RE.match(w["text"])
             and min_top <= w["top"] < max_top]
    if not codes:
        return []
    codes.sort(key=lambda w: w["top"])
    tops = [c["top"] for c in codes]
    lo = [(tops[0]-12 if i == 0 else (tops[i-1]+tops[i])/2) for i in range(len(codes))]
    hi = [(1e9 if i == len(codes)-1 else (tops[i]+tops[i+1])/2) for i in range(len(codes))]
    groups = [(c["text"], []) for c in codes]
    for w in words:
        if w["text"] in FOOTER_WORDS or is_header(w):
            continue
        top = w["top"]
        if top < 45 or top > 800 or top < min_top or top >= max_top:
            continue
        for i in range(len(codes)):
            if lo[i] <= top < hi[i]:
                if w["x0"] < 82 and CODE_RE.match(w["text"]):
                    break  # skip the anchor code itself
                groups[i][1].append(w)
                break
    return groups

def col_text(wlist, x0, x1):
    toks = sorted([w for w in wlist if x0 <= w["x0"] < x1], key=lambda w: (round(w["top"]), w["x0"]))
    return re.sub(r"\s+", " ", " ".join(w["text"] for w in toks)).strip()

# ---------- SINONIMIAS ----------
def parse_sinonimias(pdf):
    pages = [(i, 0, 1e9) for i in (19, 20, 21)] + \
            [(69, 390, 1e9)] + [(i, 0, 1e9) for i in (70, 71, 72)]
    syn = defaultdict(list)
    for pi, mn, mx in pages:
        for code, wl in bands(pdf.pages[pi], mn, mx):
            name = col_text(wl, 82, 430)
            name = re.sub(r"NBU|CUBRA|Página \d+|Confederación.*", "", name).strip(" -")
            if name:
                syn[code].append(name)
    return {k: sorted(set(v)) for k, v in syn.items()}

# ---------- ABREVIATURAS ----------
def parse_abreviaturas(pdf):
    pages = [(i, 0, 1e9) for i in (22, 23, 24, 25)] + [(26, 0, 343)] + \
            [(i, 0, 1e9) for i in range(73, 81)] + [(81, 0, 249)]
    abbr = defaultdict(list)
    for pi, mn, mx in pages:
        for code, wl in bands(pdf.pages[pi], mn, mx):
            ab = col_text(wl, 460, 600)
            if ab:
                for part in re.split(r"\s*/\s*|\s+o\s+|\s{2,}", ab):
                    part = part.strip(" .")
                    if part and part not in abbr[code]:
                        abbr[code].append(part)
    return {k: v for k, v in abbr.items()}

# ---------- NORMAS + RELATIONSHIPS ----------
REL_TRIGGERS = [
    ("included_in", re.compile(r"incluido[/\s]", re.I)),
    ("excludes",    re.compile(r"no\s+incluye", re.I)),
    ("includes",    re.compile(r"incluye", re.I)),
]

def extract_relations(text):
    """State-machine: assign 66xxxx codes to includes/excludes/included_in by preceding trigger."""
    rel = {"includes": [], "excludes": [], "included_in": []}
    tokens = text.split()
    label = None
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        low = tok.lower()
        two = (low + " " + tokens[i+1].lower()) if i+1 < len(tokens) else low
        if two.startswith("no incluye"):
            label = "excludes"; i += 2; continue
        if low.startswith("incluido"):
            label = "included_in"; i += 1; continue
        if low.startswith("incluye"):
            label = "includes"; i += 1; continue
        m = re.findall(r"66\d{4}", tok)
        if m and label:
            for c in m:
                if c not in rel[label]:
                    rel[label].append(c)
        # a period that ends a code list clears the label (avoid bleeding into next sentence w/o trigger)
        if tok.endswith(".-") or (tok.endswith(".") and re.search(r"66\d{4}", tok)):
            label = None
        i += 1
    return rel

def parse_normas(pdf):
    page_ranges = list(range(27, 38)) + [38] + list(range(82, 89))
    out = {}
    for pi in page_ranges:
        for code, wl in bands(pdf.pages[pi]):
            practica = col_text(wl, 82, 202)
            norma = col_text(wl, 202, 376)
            interp = col_text(wl, 376, 600)
            full = (norma + " " + interp).strip()
            if not full:
                continue
            rel = extract_relations(full)
            rel["includes"] = [c for c in rel["includes"] if c != code]
            rel["excludes"] = [c for c in rel["excludes"] if c != code]
            rel["included_in"] = [c for c in rel["included_in"] if c != code]
            rec = {"practica": practica, "norma": norma, "interpretacion": interp, **rel}
            # keep the richest record if code repeats across pages
            if code not in out or len(full) > len(out[code]["norma"] + out[code]["interpretacion"]):
                out[code] = rec
    return out

def main():
    pdf = pdfplumber.open(PDF)
    syn = parse_sinonimias(pdf)
    abbr = parse_abreviaturas(pdf)
    normas = parse_normas(pdf)
    print(f"sinonimias: {len(syn)} codes, {sum(len(v) for v in syn.values())} synonyms", file=sys.stderr)
    print(f"abreviaturas: {len(abbr)} codes", file=sys.stderr)
    print(f"normas: {len(normas)} codes", file=sys.stderr)
    rels = sum(len(n['includes'])+len(n['excludes'])+len(n['included_in']) for n in normas.values())
    print(f"relationships extracted: {rels}", file=sys.stderr)
    json.dump({"sinonimias": syn, "abreviaturas": abbr, "normas": normas},
              open("intel.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
