#!/usr/bin/env python3
"""Deja la base lista para que la app la cargue.

Dos modos:

    python3 scripts/inject_db.py              # publicación: escribe web/nbu_db.bin
    python3 scripts/inject_db.py --embebido   # un solo archivo: la mete en el HTML

**Publicación (lo normal).** La base va comprimida en un archivo aparte al lado del
index.html y la app la busca al arrancar. Para meterla DENTRO del HTML hay que
escribirla como texto —base64—, y eso la engorda un tercio: 776 KB pasaban a
1.034 KB. Sacándola afuera, ese tercio no se descarga nunca. Sin internet la app
sigue funcionando igual: el service worker guarda los dos archivos juntos.

**Embebido.** Deja la app como un archivo único que se puede mandar por correo o
abrir con doble clic desde el escritorio, sin servidor. Pesa más y no es lo que se
publica, pero es la vuelta atrás si algún día hace falta.

Los dos modos conviven: la app usa la base embebida si la encuentra, y si no,
busca el archivo. Cambiar de uno a otro es correr este script y publicar.
"""
import re, gzip, base64, sys, os

HTML = "web/index.html"
DB   = "data/nbu_db.json"
BIN  = "web/nbu_db.bin"
# Sin extensión conocida a propósito: con «.gz» algunos servidores agregan
# Content-Encoding por su cuenta, el navegador descomprime solo y la app se
# encuentra con un texto donde esperaba un gzip. Así nadie interpreta nada.

BLOQUE = re.compile(r'<script id="nbu-db(?:-gz)?"[^>]*>.*?</script>', re.S)
VACIO  = ('<!-- La base viaja aparte, en nbu_db.bin (ver scripts/inject_db.py). Este bloque\n'
          '     queda vacío a propósito: con «--embebido» se llena y la app pasa a ser un\n'
          '     archivo único. -->\n'
          '<script id="nbu-db-gz" type="text/plain"></script>')

def main():
    embebido = "--embebido" in sys.argv
    raw = open(DB, "rb").read()
    gz  = gzip.compress(raw, 9)
    html = open(HTML, encoding="utf-8").read()

    if embebido:
        b64 = base64.b64encode(gz).decode("ascii")
        nuevo, n = BLOQUE.subn(f'<script id="nbu-db-gz" type="text/plain">{b64}</script>', html, count=1)
        if n != 1:
            print("ERROR: no está el bloque de la base en el HTML", file=sys.stderr); sys.exit(1)
        open(HTML, "w", encoding="utf-8").write(nuevo)
        if os.path.exists(BIN):
            os.remove(BIN)   # o quedarían dos bases y una de las dos vieja
        print(f"embebida · JSON {len(raw)/1e6:.2f} MB -> gzip {len(gz)/1e6:.2f} MB -> "
              f"base64 {len(b64)/1e6:.2f} MB · HTML {len(nuevo)/1e6:.2f} MB")
        return

    open(BIN, "wb").write(gz)
    nuevo, n = BLOQUE.subn(VACIO, html, count=1)
    if n != 1:
        print("ERROR: no está el bloque de la base en el HTML", file=sys.stderr); sys.exit(1)
    open(HTML, "w", encoding="utf-8").write(nuevo)
    print(f"aparte · JSON {len(raw)/1e6:.2f} MB -> {BIN} {len(gz)/1e6:.2f} MB · "
          f"HTML {len(nuevo)/1e6:.2f} MB (antes {len(html)/1e6:.2f} MB)")

main()
