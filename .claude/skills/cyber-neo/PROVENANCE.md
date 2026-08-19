# Procedencia — código de terceros

Este directorio **no** es código de VISITAR. Es una copia (vendored) de una skill
externa, incluida en el repo para que sobreviva a sesiones efímeras de Claude Code.

| | |
|---|---|
| Origen | https://github.com/Hainrixz/cyber-neo |
| Commit fijado | `dcac0a8f111954e543e1e66e02a222c0c489ca74` (2026-07-17) |
| Subdirectorio copiado | `skills/cyber-neo/` |
| Versión del plugin | 0.1.0 |
| Autor declarado | mhenry |
| Licencia | MIT (ver `LICENSE.upstream`) |

## Qué hace

Auditoría de seguridad: SAST, SCA, detección de secretos, authn/authz, criptografía,
misconfiguraciones, supply chain y CI/CD, contra OWASP Top 10 y CWE Top 25.
Se invoca con `/cyber-neo [ruta]`.

El análisis lo hace Claude leyendo `references/`; los dos scripts de Python solo
hacen trabajo por lotes (regex sobre muchos archivos, chequeo de lock files).

## Revisión hecha antes de incluirla

- Ambos scripts de `scripts/` leídos por completo: sin red, sin `eval`/`exec`.
  La única llamada a `subprocess` es `git diff --cached --name-only`.
- Los 14 archivos de `references/` **no** fueron auditados línea por línea.
  Se cargan en el contexto de Claude durante un escaneo, así que son superficie
  de prompt injection. Revisalos si te importa ese riesgo.
- Sin señal de reputación verificable del repo upstream. Es código no auditado
  de un tercero.

## Actualizar

No hay un `git pull` que sirva acá: esto es una copia, no un submódulo.
Para actualizar, cloná el upstream, revisá el diff y volvé a copiar
`skills/cyber-neo/` sobre este directorio, actualizando el commit fijado arriba.

## Herramientas externas (opcionales)

La skill usa escáneres si están en el PATH, y degrada a análisis de Claude si no:
`semgrep`, `trivy`, `gitleaks`, `npm audit`, `pip-audit`, `cargo audit`.
Ninguno está instalado en el contenedor remoto por defecto.
