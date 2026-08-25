#!/usr/bin/env bash
#
# Prueba las reglas de acceso de docs/supabase.sql contra un PostgreSQL real.
#
# Uso:
#   tests/rls/correr.sh                    # usa PGHOST/PGPORT/PGUSER del entorno
#   PGPORT=5433 tests/rls/correr.sh
#
# Corre tres escenarios:
#   1. Instalación desde cero con supabase.sql
#   2. La misma, más la migración de seguridad encima (tiene que ser inocua)
#   3. La migración aplicada dos veces (tiene que ser idempotente)
#
# En cada uno pasa los seis ataques y las pruebas de regresión. Cualquier
# «raise exception» de los archivos .sql corta con ON_ERROR_STOP y devuelve
# distinto de cero.

set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(cd "$AQUI/../.." && pwd)"

# Los archivos de instalación son idempotentes y llenan la salida de
# «policy ... does not exist, skipping». Es ruido esperado, no un problema.
export PGOPTIONS="${PGOPTIONS:--c client_min_messages=warning}"
export PGHOST="${PGHOST:-localhost}"
export PGPORT="${PGPORT:-5432}"
export PGUSER="${PGUSER:-postgres}"
export PGDATABASE="${PGDATABASE:-postgres}"

P() { psql -v ON_ERROR_STOP=1 -q --no-psqlrc "$@"; }

limpiar() {
  P -c "drop schema if exists public cascade; drop schema if exists auth cascade; create schema public;" >/dev/null
  P -f "$AQUI/entorno.sql" >/dev/null
}

escenario() {
  local titulo="$1"; shift
  echo ""
  echo "══════════════════════════════════════════════════════════════════"
  echo "  $titulo"
  echo "══════════════════════════════════════════════════════════════════"
  limpiar
  for archivo in "$@"; do
    P -f "$archivo" >/dev/null
  done
  P -f "$AQUI/datos.sql" >/dev/null
  P -f "$AQUI/ataques.sql"
  P -f "$AQUI/regresion.sql"
}

escenario "1. Instalación desde cero" \
  "$RAIZ/docs/supabase.sql"

escenario "2. Con las migraciones encima" \
  "$RAIZ/docs/supabase.sql" "$RAIZ/docs/supabase_seguridad.sql" "$RAIZ/docs/supabase_auditoria.sql" \
  "$RAIZ/docs/supabase_relaciones_medico.sql" "$RAIZ/docs/supabase_sugerencias_pedida_como.sql"

escenario "3. Migraciones aplicadas dos veces (idempotencia)" \
  "$RAIZ/docs/supabase.sql" "$RAIZ/docs/supabase_seguridad.sql" "$RAIZ/docs/supabase_auditoria.sql" \
  "$RAIZ/docs/supabase_relaciones_medico.sql" "$RAIZ/docs/supabase_sugerencias_pedida_como.sql" \
  "$RAIZ/docs/supabase_seguridad.sql" "$RAIZ/docs/supabase_auditoria.sql" \
  "$RAIZ/docs/supabase_relaciones_medico.sql" "$RAIZ/docs/supabase_sugerencias_pedida_como.sql"

echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "  Todo en verde: 10 ataques bloqueados y la app sigue funcionando,"
echo "  en los tres escenarios."
echo "══════════════════════════════════════════════════════════════════"
