#!/bin/bash
# Recuerda, al arrancar cada sesión, la regla del punto 13 de HANDOFF.md:
# tocar web/index.html sin resellar la CSP deja la app colgada en "Cargando
# base…" sin ningún error visible (ya costó un ciclo de depuración completo,
# 16/8/2026). No instala nada — el repo no tiene manifiesto de dependencias
# (scripts/sellar_csp.py es stdlib puro) — solo confirma que el script está
# y deja la regla escrita en el contexto de la sesión.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

if command -v python3 >/dev/null 2>&1 && [ -f scripts/sellar_csp.py ]; then
  estado="scripts/sellar_csp.py disponible (python3 $(python3 -c 'import sys;print(".".join(map(str,sys.version_info[:3])))'))."
else
  estado="⚠ No encontré scripts/sellar_csp.py o falta python3 — revisar antes de tocar web/index.html."
fi

cat <<EOF
REGLA DEL REPO (HANDOFF.md, punto 13) — VISITAR:
Si esta sesión edita <script> dentro de web/index.html (contenido o cantidad
de bloques inline), correr ANTES de terminar:

    python3 scripts/sellar_csp.py

La CSP de la app fija los hashes SHA de cada <script> inline. Si el archivo
cambia y el sellado no se vuelve a correr, el navegador rechaza ejecutar
TODOS los scripts (CSP desactualizada) — sin ningún error visible: la
pantalla de arranque "Cargando base…" queda colgada para siempre, y un test
de Playwright muere a los 30s en el waitForFunction del #boot, como si fuera
lento. No hace falta correrlo si solo se tocó CSS/HTML sin scripts.

$estado
EOF
