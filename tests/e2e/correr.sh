#!/usr/bin/env bash
# Corre todos los casos de tests/e2e/casos/*.mjs y falla si alguno falla.
# No usa `set -e`: un caso que falla no puede cortar la corrida antes de que
# se prueben los demás, si no un solo fallo esconde al resto.
set -uo pipefail
cd "$(dirname "$0")"

if [ ! -d node_modules/playwright ]; then
  echo "Falta node_modules/playwright — correr 'npm install' en tests/e2e/ primero." >&2
  exit 1
fi

fallo=0
for caso in casos/*.mjs; do
  echo "== $caso =="
  if ! node "$caso"; then fallo=1; fi
  echo
done

exit "$fallo"
