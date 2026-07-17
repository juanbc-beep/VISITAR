# Manual Inteligente Unificado de Códigos Médicos

Herramienta para consultar, interpretar y **facturar correctamente** los códigos de los
nomencladores médicos argentinos, con relaciones entre códigos y reglas de auditoría por práctica.

Estado actual: cargados **dos nomencladores relacionados** en una sola base (**2.611 códigos**):

- **NBU — Nomenclador Bioquímico Único** (Versión 2012 · Actualización 2016, CUBRA) — 1.377 códigos, con el
  **Anexo Enero 2024** de U.B. revalorizadas aplicado como overlay.
- **Catálogo de Prestaciones del PMO** (Resolución 201/2002, S.S. Salud) — 1.234 prestaciones médicas y
  quirúrgicas por especialidad.

Ambos se cruzan: **315 códigos de laboratorio (66xxxx)** aparecen en los dos nomencladores y quedan
enlazados (en la ficha del NBU se marca "También en Catálogo PMO").

## Qué incluye

### NBU (bioquímica) — 1.377 prácticas
- Clasificación oficial:
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
- Clasificación **orientativa** por grupo/especialidad para facilitar la navegación
  (el NBU es alfabético; la clasificación oficial es la sección PMO/PE/Gestión).

### Catálogo PMO (prestaciones médicas) — 1.234 códigos
- Prestaciones médicas y quirúrgicas por **capítulo/especialidad** (código de 6 dígitos):
  cirugía (sistema nervioso, cardiovascular, digestivo, traumatología, etc.), diagnóstico por imágenes,
  cardiología, neurología, hemoterapia, medicina nuclear, radioterapia, laboratorio, y más (~36 capítulos).
- Son prestaciones de **cobertura obligatoria** del PMO; el arancel surge del nomenclador/convenio aplicable
  (el catálogo lista qué se cubre, no valores monetarios).
- **Valores del Nomenclador Nacional** (Anexo II, Res. 201/02) para **674 códigos quirúrgicos**, extraídos por
  **OCR** de los PDF escaneados y **validados por checksum** (los 4 valores en $ suman el Total; 95% de las
  filas con precio pasan la validación). Cada código trae, en **galenos** y en **$ de referencia 2002**:
  honorarios de **especialista**, **ayudantes** (con Nº que admite), **anestesista**, **gasto** y **total**.
- Cada ficha médica incluye **"Asociación de códigos · qué cargar"**: para los códigos con valores, las
  asociaciones son **específicas** (cuántos ayudantes admite, si lleva anestesia y sus galenos, gasto);
  para el resto, **normas generales por capítulo** (cirujano + ayudantes + gastos + anestesia cap. 16 +
  anatomía patológica cap. 15). Marcadas como **orientativas** (verificar contra la norma aplicable).
- El pipeline OCR (`scripts/ocr_nn.py` + `scripts/parse_nn.py`) es reutilizable para la 3ª parte del
  Nomenclador (prácticas y consultas), pendiente de carga.

### Odontología (Nomenclador Nacional dental) — 79 códigos
- Prácticas odontológicas (Anexo II, Res. 201/02) por capítulo: consultas, operatoria dental, endodoncia,
  prótesis, periodoncia, ortodoncia, cirugía bucal, etc.
- Valorización por **OCR validada por checksum** (Honorarios$ + Gasto$ = Valor Práctica; 86% de las filas
  con precio validan): honorarios y gasto en **galenos odontológicos** + **$ ref. 1991** + **coseguro máximo %**.
- Nota: los nombres de las prácticas dentales pueden tener artefactos de OCR (el escaneo perdió espacios);
  código, valores y coseguro son correctos.

La interfaz separa **tres secciones** con un selector principal: **Laboratorio (NBU)**, **Prestaciones
médicas (PMO)** y **Odontología** — en cada una solo se ven sus códigos, grupos y determinaciones (no se mezclan).

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
  parse_catalog.py      # Parser del catálogo NBU (coordenadas) -> catalog.json
  parse_intel.py        # Parser de sinonimias, abreviaturas y normas NBU (tablas) -> intel.json
  parse_pmo.py          # Parser del Catálogo PMO (2 columnas) -> pmo_catalog.json
  assemble.py           # Une NBU + PMO, clasifica, cruza 66xxxx, genera reglas -> nbu_db.json
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
