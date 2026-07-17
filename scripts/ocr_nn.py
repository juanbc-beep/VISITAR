#!/usr/bin/env python3
"""OCR the scanned Nomenclador Nacional (rotated) and cache results per page to JSON."""
import sys, json, time
import pypdfium2 as pdfium
from rapidocr_onnxruntime import RapidOCR

pdf_path, out_path = sys.argv[1], sys.argv[2]
ROT = int(sys.argv[3]) if len(sys.argv) > 3 else -90
ocr = RapidOCR()
pdf = pdfium.PdfDocument(pdf_path)
n = len(pdf)
pages = []
t0 = time.time()
for i in range(n):
    img = pdf[i].render(scale=3.0).to_pil()
    if ROT:
        img = img.rotate(ROT, expand=True)
    res, _ = ocr(img)
    toks = []
    if res:
        for box, txt, conf in res:
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            toks.append([round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1), txt, round(float(conf), 3)])
    pages.append({"page": i + 1, "w": img.size[0], "h": img.size[1], "toks": toks})
    if (i + 1) % 5 == 0 or i == n - 1:
        el = time.time() - t0
        print(f"  {i+1}/{n} pages  ({el:.0f}s, {el/(i+1):.1f}s/pg)", flush=True)
    json.dump(pages, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
print(f"DONE {out_path}: {n} pages, {sum(len(p['toks']) for p in pages)} tokens", flush=True)
