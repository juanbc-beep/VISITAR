#!/usr/bin/env python3
"""Renderiza las páginas del Nomenclador Nacional recortadas a lo que hay que leer.

    python3 scripts/paginas_nn.py 97 98 99
    python3 scripts/paginas_nn.py 20        # el capítulo entero, según data/paginas_nn.json

⚠️ POR QUÉ EL RECORTE. Estas páginas se leen a ojo —el PDF es un escaneo sin capa
de texto— y cada imagen que entra a la conversación se reenvía en TODOS los
pedidos siguientes. No es un costo que se paga una vez: la primera página de una
sesión larga se manda decenas de veces.

La mitad derecha de la página son las columnas de honorarios, gastos y total,
que NO se transcriben: lo que se lee es el código y la descripción con su
recuadro «Texto retirado por el PMO». Recortando ahí:

    página entera : 1550x1096 → ~2.265 tokens de visión
    recorte       :  976x921  → ~1.199 tokens   (47% menos)

Verificado que la bastardilla del texto retirado se sigue leyendo igual.

⚠️ El borde derecho va en 0,685 y no menos: la columna de descripción llega más
a la derecha de lo que parece, y con 0,60 se cortan las normas largas a mitad de
frase («no incluyen el costo de las sustan…»). Se probó y se corrigió.
"""
import json, os, sys
import pypdfium2 as pdfium

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(BASE, "data",
                   "NOMENCLADOR NACIONAL DE PRESTACIONES MEDICAS CON PMO-COMPRIMIDO.pdf")
INDICE = os.path.join(BASE, "data", "paginas_nn.json")

ESCALA = 2.3
CAJA = (0.055, 0.06, 0.685, 0.90)      # izq, arriba, der, abajo — en proporción


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)

    paginas = []
    caps = json.load(open(INDICE, encoding="utf-8"))["capitulos"]
    for a in args:
        if a in caps:                                   # es un capítulo
            ini, fin = caps[a]["pags"]
            paginas += list(range(ini, fin + 1))
        else:
            paginas.append(int(a))

    salida = os.environ.get("SALIDA", "/tmp/nn")
    os.makedirs(salida, exist_ok=True)
    pdf = pdfium.PdfDocument(PDF)
    for n in paginas:
        im = pdf[n].render(scale=ESCALA).to_pil()
        w, h = im.size
        rec = im.crop((int(w * CAJA[0]), int(h * CAJA[1]),
                       int(w * CAJA[2]), int(h * CAJA[3])))
        destino = os.path.join(salida, "p%d.png" % n)
        rec.save(destino)
        print("  %s  %dx%d  ~%d tokens" % (destino, rec.size[0], rec.size[1],
                                           rec.size[0] * rec.size[1] / 750))
    print("\n%d página(s). Enteras habrían sido ~%d tokens; recortadas, ~%d."
          % (len(paginas), len(paginas) * 2265, len(paginas) * 1199))


if __name__ == "__main__":
    main()
