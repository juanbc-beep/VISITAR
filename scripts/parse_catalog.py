#!/usr/bin/env python3
"""Coordinate-based parser for the NBU main catalog (PMO, Gestion, Practicas Especiales)."""
import pdfplumber, re, json, sys

PDF = "/root/.claude/uploads/ac5e0c28-47d1-5f23-85ef-4bdfc9a090ce/f839a468-NBUVersion2012Act.2016.pdf"

# section -> list of (0-based page index, max_top cutoff)
CATALOG_PAGES = {
    "PMO": [(i, 1e9) for i in range(8, 19)],          # pages 9-19
    "GESTION": [(38, 1e9)],                            # page 39 (only the 2 admin codes)
    "PE": [(i, 1e9) for i in range(39, 69)] + [(69, 360)],  # pages 40-69 + top of 70
}

CODE_RE = re.compile(r"^66\d{4}$")
FOOTER = "CTP - NBU - CUBRA"

def clean(tokens):
    return " ".join(t["text"] for t in tokens)

def parse_page(page, section, max_top=1e9):
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    # column-header row tops (the "CÓDIGO ... Urgencia Ref. U. B." line) to drop
    header_tops = [w["top"] for w in words if w["text"] == "CÓDIGO"]
    def is_header(w):
        return any(abs(w["top"] - h) < 4 for h in header_tops)
    # locate code anchors in the CODE column (above the max_top cutoff)
    codes = [w for w in words if w["x0"] < 82 and CODE_RE.match(w["text"]) and w["top"] < max_top]
    if not codes:
        return []
    codes.sort(key=lambda w: w["top"])
    tops = [c["top"] for c in codes]
    # vertical band boundaries (midpoints between consecutive codes)
    # first code's lower bound is capped just above it to exclude page title/header block
    lo = [(tops[0]-12 if i == 0 else (tops[i-1]+tops[i])/2) for i in range(len(codes))]
    hi = [(1e9 if i == len(codes)-1 else (tops[i]+tops[i+1])/2) for i in range(len(codes))]
    rows = [{"code": c["text"], "name": [], "urg": [], "ref": [], "ub": []} for c in codes]

    for w in words:
        t = w["text"]
        if t == FOOTER or "CTP" == t:
            continue
        top = w["top"]; x0 = w["x0"]
        # skip page header band, footer band, cutoff region, and column-header row
        if top < 45 or top > 795 or top >= max_top or is_header(w):
            continue
        # find band
        idx = None
        for i in range(len(codes)):
            if lo[i] <= top < hi[i]:
                idx = i; break
        if idx is None:
            continue
        # column assignment by x0
        if x0 < 82:
            if CODE_RE.match(t):
                continue  # it's the code anchor itself
            # stray token in code column -> treat as name fragment
            rows[idx]["name"].append(w)
        elif x0 < 430:
            rows[idx]["name"].append(w)
        elif x0 < 478:
            rows[idx]["urg"].append(w)
        elif x0 < 522:
            rows[idx]["ref"].append(w)
        else:
            rows[idx]["ub"].append(w)

    out = []
    for r in rows:
        name_tokens = sorted(r["name"], key=lambda w: (round(w["top"]), w["x0"]))
        name = " ".join(w["text"] for w in name_tokens)
        # strip page header/footer remnants that can leak into first/last rows
        name = re.sub(r"(CTP\s*)?-?\s*NBU\s*-\s*CUBRA", "", name)
        name = re.sub(r"CUBRA\s*-\s*Confederación.*?Argentina\s*-?\s*Página\s*\d+", "", name)
        name = re.sub(r"Página\s*\d+\s*-\s*CUBRA.*?Argentina", "", name)
        # truncate at any section-header phrase that may leak from below (ascii-only markers)
        name = re.split(r"NORMAS ESPEC|ANEXO DE |NOMENCLADOR BIO|GESTION ADMIN", name)[0]
        name = re.sub(r"\s+", " ", name).strip(" -")
        urg = "U" if any(w["text"] == "U" for w in r["urg"]) else ""
        ref_texts = [w["text"] for w in sorted(r["ref"], key=lambda w:(round(w["top"]),w["x0"]))]
        norma_flag = "N" in ref_texts
        desuso = any("#" in x for x in ref_texts)
        ref_nums = [x for x in ref_texts if re.match(r"^\d{3,4}$", x)]
        ub_texts = [w["text"] for w in sorted(r["ub"], key=lambda w:(round(w["top"]),w["x0"]))]
        ub_raw = " ".join(ub_texts).strip()
        # UB may capture a stray '(#)' or '-' ; interpret
        ub_val = None
        m = re.search(r"(\d+(?:,\d+)?)", ub_raw)
        if m:
            ub_val = float(m.group(1).replace(",", "."))
        out.append({
            "code": r["code"], "section": section, "name": name,
            "urgencia": bool(urg), "norma": norma_flag, "desuso": desuso,
            "ref_nums": ref_nums, "ub": ub_val, "ub_raw": ub_raw,
        })
    return out

def main():
    pdf = pdfplumber.open(PDF)
    all_rows = []
    for section, pages in CATALOG_PAGES.items():
        for pi, cutoff in pages:
            rows = parse_page(pdf.pages[pi], section, cutoff)
            # GESTION page 39 also contains the norms table (same codes, no UB) -> keep only catalog rows
            if section == "GESTION":
                rows = [r for r in rows if r["ub"] is not None]
            all_rows.extend(rows)
    # sanity
    seen = {}
    dups = []
    for r in all_rows:
        if r["code"] in seen:
            dups.append(r["code"])
        seen[r["code"]] = r
    print(f"TOTAL rows: {len(all_rows)}  unique: {len(seen)}  dups: {dups[:20]}", file=sys.stderr)
    by_sec = {}
    for r in all_rows:
        by_sec[r["section"]] = by_sec.get(r["section"], 0) + 1
    print("by section:", by_sec, file=sys.stderr)
    # count anomalies: empty name or missing ub
    noname = [r["code"] for r in all_rows if not r["name"]]
    noub = [r["code"] for r in all_rows if r["ub"] is None]
    print(f"empty name: {len(noname)} {noname[:20]}", file=sys.stderr)
    print(f"no ub value (desuso/-): {len(noub)} e.g. {noub[:15]}", file=sys.stderr)
    with open("catalog.json", "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
