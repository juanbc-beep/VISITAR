#!/usr/bin/env python3
"""Reemplaza «unsafe-inline» de script-src por la huella de cada script.

Por qué existe:
    La política de seguridad decía  script-src 'self' 'unsafe-inline'.  Ese
    permiso es lo que vuelve explotable un agujero de inyección: si alguien
    logra meter un <script> en la página, el navegador lo ejecuta. Con huellas,
    el navegador sólo ejecuta los scripts que ya estaban cuando se publicó;
    cualquier otro, aunque se inyecte con éxito, no corre.

    No se hace a mano porque la acción de publicación reescribe el archivo
    (sella el commit y la versión del service worker) y eso cambia la huella.
    Este paso corre DESPUÉS de esos, como último eslabón del armado.

    «style-src» conserva 'unsafe-inline' a propósito: la app usa atributos
    style= en cientos de lugares y las huellas no los cubren. Inyectar estilo
    es mucho menos grave que inyectar código, y sacarlo pediría reescribir
    media interfaz.

Uso:  python3 scripts/sellar_csp.py [web/index.html]
"""
import base64, hashlib, re, sys

ARCHIVO = sys.argv[1] if len(sys.argv) > 1 else "web/index.html"

# Tipos que el navegador ejecuta. Un <script type="text/plain"> (la base de
# datos embebida) no se ejecuta, así que no lleva huella ni le aplica la regla.
EJECUTABLES = {"", "text/javascript", "application/javascript", "module"}

BLOQUE = re.compile(r"<script([^>]*)>(.*?)</script>", re.S | re.I)
TIPO   = re.compile(r"""\btype\s*=\s*["']?([^"'\s>]+)""", re.I)


def huellas(html):
    out = []
    for attrs, cuerpo in BLOQUE.findall(html):
        m = TIPO.search(attrs)
        tipo = (m.group(1).lower() if m else "")
        if tipo not in EJECUTABLES:
            continue
        if not cuerpo.strip():          # <script src=…> no lleva huella
            continue
        d = hashlib.sha256(cuerpo.encode("utf-8")).digest()
        out.append("'sha256-" + base64.b64encode(d).decode() + "'")
    return out


def main():
    with open(ARCHIVO, encoding="utf-8") as f:
        html = f.read()

    hs = huellas(html)
    if not hs:
        sys.exit("sellar_csp: no se encontró ningún script ejecutable — abortado")

    nueva = "script-src 'self' " + " ".join(hs) + ";"
    html2, n = re.subn(r"script-src[^;]*;", nueva, html, count=1)
    if n != 1:
        sys.exit("sellar_csp: no se encontró la directiva script-src — abortado")

    # Control: las huellas se calculan sobre el texto YA escrito. Si el
    # reemplazo hubiera tocado un script, quedarían mal y la app no arrancaría.
    if huellas(html2) != hs:
        sys.exit("sellar_csp: el reemplazo alteró un script — abortado")

    with open(ARCHIVO, "w", encoding="utf-8") as f:
        f.write(html2)

    print(f"sellar_csp: {len(hs)} script(s) sellado(s) en {ARCHIVO}")
    for h in hs:
        print("   ", h)


if __name__ == "__main__":
    main()
