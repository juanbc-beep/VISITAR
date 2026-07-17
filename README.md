# Manual Inteligente Unificado de Códigos Médicos

Herramienta para consultar, interpretar y **facturar correctamente** los códigos de los
nomencladores médicos argentinos, con relaciones entre códigos y reglas de auditoría por práctica.

Estado actual: cargado el **NBU — Nomenclador Bioquímico Único** (Versión 2012 · Actualización 2016, CUBRA),
con el **Anexo Enero 2024** de U.B. revalorizadas aplicado como overlay. El **Nomenclador Nacional de
Prestaciones Médicas** se incorporará en una próxima carga (el modelo de datos ya lo contempla vía el campo `nomenclador`).

## Qué incluye

- **1.377 prácticas** del NBU, divididas en su clasificación oficial:
  - **PMO** (Programa Médico Obligatorio) — 370
  - **Prácticas Especiales (P.E.)** — 1.005
  - **Gestión Administrativa** — 2
- Por cada código:
  - **Nombre**, **U.B.** (Unidad Bioquímica) y fórmula de arancel.
  - **Sinónimos** (149) y **abreviaturas** (399 códigos) para búsqueda.
  - **Flags**: urgencia (`U`), requiere norma (`N`), en desuso (`#`), metodología PCR.
  - **Norma e interpretación** oficial (texto), para 140 códigos.
  - **Relaciones entre códigos** (197 códigos): *incluye* / *no incluye* / *incluido en*.
  - **Normas de auditoría / facturación** generadas por código (qué no facturar por separado, cuándo adicionar 661200, etc.).
  - **U.B. actualizada 2024** donde el anexo la revaloriza (50 códigos).
- **Glosario** de referencias y flags + **marco normativo** (12 leyes vigentes).
- Clasificación **orientativa** por grupo/especialidad (15 grupos) para facilitar la navegación
  (el NBU es alfabético; la clasificación oficial es la sección PMO/PE/Gestión).

## Uso

Abrí **`web/index.html`** en cualquier navegador (no requiere servidor ni conexión — la base va embebida).

Tres vistas (pestañas):
- **Listado** — buscá por código, práctica, sinónimo o abreviatura; filtrá por sección, grupo o reglas/estados. Detalle con **códigos relacionados clickeables** que navegan entre sí. Enlace directo por hash: `index.html#660475`.
- **Árbol de módulos** — jerarquía expandible de los módulos de facturación (qué incluye cada código y no debe facturarse por separado).
- **Validador de facturación** — pegás una lista de códigos (con cantidades `×N`) y detecta doble facturación por inclusión, urgencias sin 661200, Acto Bioquímico faltante, seriados excedidos, desuso e inexistentes; calcula U.B. netas y arancel.

Funciones operativas:
- **Valor de la U.B.** (arriba): al cargarlo, se muestra el **arancel** ($) en el listado, la ficha y el validador. Se guarda en el navegador.
- **Favoritos** (★): marcá códigos frecuentes; se guardan y se filtran con “★ Favoritos”.
- **Exportar**: descargá a **CSV** (listado y validación) o **Imprimí/PDF** desde el navegador.
- **Frecuencia/seriado**: los códigos con reglas de seriado (p. ej. `660102`, `660468`) las muestran en la ficha y el validador las controla.

## Estructura del repositorio

```
data/
  nbu_db.json           # Base de datos unificada (fuente de verdad) — 1.377 códigos
  nbu_catalog_raw.json  # Catálogo crudo parseado (intermedio)
  nbu_intel_raw.json    # Sinonimias / abreviaturas / normas crudas (intermedio)
scripts/
  parse_catalog.py      # Parser del catálogo (coordenadas) -> catalog.json
  parse_intel.py        # Parser de sinonimias, abreviaturas y normas (tablas) -> intel.json
  assemble.py           # Une todo, clasifica grupos, genera reglas -> nbu_db.json
web/
  index.html            # Aplicación web autocontenida (base embebida)
```

## Modelo de datos (`nbu_db.json`)

```jsonc
{
  "meta":     { "total_codigos": 1377, "secciones": {...}, "grupos": {...} },
  "glosario": { "U": "...", "N": "...", "(#)": "...", "661200": "..." },
  "leyes":    [ { "ley": "27232", "titulo": "Ley NBU", "sancion": "26/11/2015" } ],
  "codigos": {
    "660475": {
      "code": "660475", "nomenclador": "NBU", "seccion": "PMO",
      "grupo": "Hematología y hemostasia", "nombre": "HEMOGRAMA.",
      "sinonimos": [...], "abreviaturas": [...],
      "valor":  { "ub": 3.0, "unidad": "U.B. (Unidad Bioquímica)", "arancel": "...", "ub_actualizado_2024": null },
      "flags":  { "urgencia": true, "requiere_norma": true, "desuso": false, "pcr": false },
      "referencias": [ { "code": "8332", "target": "668332", "texto": "..." } ],
      "norma":  { "trabajo": "...", "interpretacion": "..." },
      "relaciones": { "incluye": ["660354", ...], "no_incluye": [], "incluido_en": [] },
      "auditoria": [ "Urgencia (U): ...", "INCLUYE (módulo): comprende ..." ]
    }
  }
}
```

### Modelo de versión / vigencia

El valor base (v2016) y el revalorizado (`ub_actualizado_2024`) conviven por código, de modo que el
histórico no se pisa. Al sumar nuevas actualizaciones alcanza con agregar otro campo de valor fechado.

## Regenerar la base

Los parsers trabajan sobre el PDF oficial del NBU (fuente externa, no versionada en el repo):

```bash
python3 scripts/parse_catalog.py   # -> catalog.json
python3 scripts/parse_intel.py     # -> intel.json
python3 scripts/assemble.py        # -> nbu_db.json   (usa nbu_reval.txt para el overlay 2024, opcional)
```

Luego se embebe `nbu_db.json` dentro de `web/index.html` (bloque `<script id="nbu-db">`).

## Notas y alcance

- La clasificación por **grupo/especialidad** es orientativa (heurística por palabras clave); la
  clasificación **oficial** es la sección (PMO/PE/Gestión). ~20% de los códigos quedan en “Otros / general”.
- Las **relaciones y reglas de auditoría** se extraen del Anexo de Normas e Interpretaciones oficial.
- Fuente: **CUBRA — Confederación Unificada Bioquímica de la República Argentina**, NBU v2012 act. 2016 + Anexo Enero 2024.
